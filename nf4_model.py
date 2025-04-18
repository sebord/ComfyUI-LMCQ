import torch
import bitsandbytes as bnb
from bitsandbytes.nn.modules import Params4bit, QuantState
import comfy.ops

def functional_linear_4bits(x, weight, bias):
    if weight.device.type == 'cuda':
        weight = weight.to(x.device)
        if bias is not None:
            bias = bias.to(x.device)
    out = bnb.matmul_4bit(x, weight.t(), bias=bias, quant_state=weight.quant_state)
    out = out.to(x.dtype)
    return out

def copy_quant_state(state: QuantState, device: torch.device = None) -> QuantState:
    if state is None:
        return None

    device = device or state.absmax.device

    state2 = (
        QuantState(
            absmax=state.state2.absmax.to(device),
            shape=state.state2.shape,
            code=state.state2.code.to(device),
            blocksize=state.state2.blocksize,
            quant_type=state.state2.quant_type,
            dtype=state.state2.dtype,
        )
        if state.nested
        else None
    )

    return QuantState(
        absmax=state.absmax.to(device),
        shape=state.shape,
        code=state.code.to(device),
        blocksize=state.blocksize,
        quant_type=state.quant_type,
        dtype=state.dtype,
        offset=state.offset.to(device) if state.nested else None,
        state2=state2,
    )

class ForgeParams4bit(Params4bit):
    def to(self, *args, **kwargs):
        device, dtype, non_blocking, convert_to_format = torch._C._nn._parse_to(*args, **kwargs)
        if device is not None and device.type == "cuda" and not self.bnb_quantized:
            return self._quantize(device)
        else:
            n = ForgeParams4bit(
                torch.nn.Parameter.to(self, device=device, dtype=dtype, non_blocking=non_blocking),
                requires_grad=self.requires_grad,
                quant_state=copy_quant_state(self.quant_state, device),
                blocksize=self.blocksize,
                compress_statistics=self.compress_statistics,
                quant_type=self.quant_type,
                quant_storage=self.quant_storage,
                bnb_quantized=self.bnb_quantized,
                module=self.module
            )
            self.module.quant_state = n.quant_state
            self.data = n.data
            self.quant_state = n.quant_state
            return n

class ForgeLoader4Bit(torch.nn.Module):
    def __init__(self, *, device, dtype, quant_type, **kwargs):
        super().__init__()
        self.dummy = torch.nn.Parameter(torch.empty(1, device=device, dtype=dtype))
        self.weight = None
        self.quant_state = None
        self.bias = None
        self.quant_type = quant_type

    def _save_to_state_dict(self, destination, prefix, keep_vars):
        super()._save_to_state_dict(destination, prefix, keep_vars)
        quant_state = getattr(self.weight, "quant_state", None)
        if quant_state is not None:
            for k, v in quant_state.as_dict(packed=True).items():
                destination[prefix + "weight." + k] = v if keep_vars else v.detach()
        return

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        quant_state_keys = {k[len(prefix + "weight."):] for k in state_dict.keys() if k.startswith(prefix + "weight.")}

        if any('bitsandbytes' in k for k in quant_state_keys):
            quant_state_dict = {k: state_dict[prefix + "weight." + k] for k in quant_state_keys}

            self.weight = ForgeParams4bit.from_prequantized(
                data=state_dict[prefix + 'weight'],
                quantized_stats=quant_state_dict,
                requires_grad=False,
                device=self.dummy.device,
                module=self
            )
            self.quant_state = self.weight.quant_state

            if prefix + 'bias' in state_dict:
                self.bias = torch.nn.Parameter(state_dict[prefix + 'bias'].to(self.dummy))

            del self.dummy
        elif hasattr(self, 'dummy'):
            if prefix + 'weight' in state_dict:
                self.weight = ForgeParams4bit(
                    state_dict[prefix + 'weight'].to(self.dummy),
                    requires_grad=False,
                    compress_statistics=True,
                    quant_type=self.quant_type,
                    quant_storage=torch.uint8,
                    module=self,
                )
                self.quant_state = self.weight.quant_state

            if prefix + 'bias' in state_dict:
                self.bias = torch.nn.Parameter(state_dict[prefix + 'bias'].to(self.dummy))

            del self.dummy
        else:
            super()._load_from_state_dict(state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs)

# Global variables for device and dtype management
current_device = None
current_dtype = None
current_manual_cast_enabled = False
current_bnb_dtype = None

# You may need to import comfy.ops or define it here
import comfy.ops

class OPS:
    class manual_cast(comfy.ops.manual_cast):
        pass
        
    class Linear(ForgeLoader4Bit):
        def __init__(self, *args, device=None, dtype=None, **kwargs):
            super().__init__(device=device, dtype=dtype, quant_type=current_bnb_dtype)
            self.parameters_manual_cast = current_manual_cast_enabled

        def forward(self, x):
            self.weight.quant_state = self.quant_state
            
            if self.weight.device != x.device:
                self.weight = self.weight.to(x.device)
            
            if self.bias is not None:
                if self.bias.device != x.device:
                    self.bias = torch.nn.Parameter(self.bias.to(x.device))
                if self.bias.dtype != x.dtype:
                    self.bias.data = self.bias.data.to(x.dtype)

            if not self.parameters_manual_cast:
                return functional_linear_4bits(x, self.weight, self.bias)
            elif not self.weight.bnb_quantized:
                assert x.device.type == 'cuda', 'BNB Must Use CUDA as Computation Device!'
                layer_original_device = self.weight.device
                self.weight = self.weight._quantize(x.device)
                bias = self.bias.to(x.device) if self.bias is not None else None
                out = functional_linear_4bits(x, self.weight, bias)
                self.weight = self.weight.to(layer_original_device)
                return out
            else:
                weight, bias, signal = weights_manual_cast(self, x, skip_weight_dtype=True, skip_bias_dtype=True)
                with main_stream_worker(weight, bias, signal):
                    return functional_linear_4bits(x, weight, bias)

    class LayerNorm(torch.nn.LayerNorm):
        def __init__(self, normalized_shape, eps=1e-5, elementwise_affine=True, dtype=None, device=None):
            super().__init__(normalized_shape, eps=eps, elementwise_affine=elementwise_affine)
            if dtype is not None or device is not None:
                self.to(device=device, dtype=dtype)
                
        def forward(self, x):
            if self.weight is not None and self.weight.device != x.device:
                self.to(x.device)
            return super().forward(x.float()).to(x.dtype)

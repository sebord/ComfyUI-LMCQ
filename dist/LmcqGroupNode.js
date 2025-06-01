import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";
import { $el } from "/scripts/ui.js"; // Use ComfyUI's standard element creation

// Use LMCQ specific names
const nodeName = "LmcqGroupNode";
const serverName = "lmcq";
const apiEndpoint = "encipher_group";
const menuLabel = "LMCQ-云加密组"; // Label remains

// --- Restore Machine Codes and add Identifier to Prompt ---
function showGroupNodeSettingsPrompt(callback) { // Renamed back
    console.log("[LMCQ Prompt] Entered showGroupNodeSettingsPrompt function (using app.ui.dialog).");

    // Create the main container for the dialog content
    const contentContainer = $el("div", {
        style: {
            padding: "20px", 
            color: "#eee", 
            minWidth: "350px",
            fontFamily: "sans-serif"
        }
    });
    console.log("[LMCQ Prompt] Created content container element:", contentContainer);

    const header = $el("div", {
        style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }
    }, [
        $el("h3", { textContent: "设置云加密组", style: { margin: "0 0 15px 0", color: "#0af" } }), // Add bottom margin
    ]);
    console.log("[LMCQ Prompt] Created header element.");

    // Identifier Input (New)
    const identifierLabel = $el("label", { textContent: "加密节点组名称:", style: { display: 'block', marginBottom: '5px'} });
    const identifierInput = $el("input", { type: "text", placeholder: "必填，例如：projectA_v1，且不可重复", style: { width: "calc(100% - 22px)", padding: "10px", marginBottom: "15px", border: "1px solid #444", borderRadius: "4px", background: "#333", color: "#eee" } });
    console.log("[LMCQ Prompt] Created identifier input.");

    // Password Input
    const passwordLabel = $el("label", { textContent: "加密密码:", style: { display: 'block', marginBottom: '5px'} });
    const passwordInput = $el("input", { type: "password", placeholder: "必填", style: { width: "calc(100% - 22px)", padding: "10px", marginBottom: "15px", border: "1px solid #444", borderRadius: "4px", background: "#333", color: "#eee" } });
    console.log("[LMCQ Prompt] Created password input.");

    // Machine Code Input (Restored)
    const machineCodeLabel = $el("label", { textContent: "授权机器码 (每行一个，留空则不限制):", style: { display: 'block', marginBottom: '5px'} });
    const machineCodeInput = $el("textarea", {
        rows: "4",
        placeholder: "留空则不限制机器码",
        style: {
            width: "calc(100% - 22px)", padding: "10px", marginBottom: "20px", border: "1px solid #444",
            borderRadius: "4px", background: "#333", color: "#eee", resize: "vertical"
        }
    });
    console.log("[LMCQ Prompt] Created machine code input.");

    // Buttons
    const buttons = $el("div", { style: { textAlign: "right", marginTop: "20px" } }); // Add top margin
    const cancelButton = $el("button", {
        textContent: "取消",
        style: {
            padding: "8px 15px", marginRight: "10px", border: "none", borderRadius: "4px",
            background: "#444", color: "#ccc", cursor: "pointer"
        }
    });
    cancelButton.onclick = () => {
        console.log("[LMCQ Prompt] Cancel button clicked.");
        app.ui.dialog.close(); // Close the ComfyUI dialog
        callback(null, null, null);
    };
    const confirmButton = $el("button", {
        textContent: "确认",
        style: {
            padding: "8px 15px", border: "none", borderRadius: "4px",
            background: "#08a", color: "#fff", cursor: "pointer"
        }
    });
    confirmButton.onclick = () => {
        console.log("[LMCQ Prompt] Confirm button clicked.");
        const identifier = identifierInput.value.trim();
        const password = passwordInput.value;
        const machineCodesText = machineCodeInput.value.trim();
        const machineCodes = machineCodesText ? machineCodesText.split(/\r?\n/).map(code => code.trim()).filter(Boolean) : [];

        if (!identifier) { alert("加密节点组名称不能为空！"); return; }
        if (!password) { alert("密码不能为空！"); return; }

        app.ui.dialog.close(); // Close the ComfyUI dialog
        callback(identifier, password, machineCodes);
    };
    // console.log("[LMCQ Prompt] Created buttons and attached onclick handlers.");

    // Append elements to the content container 
    // console.log("[LMCQ Prompt] Appending buttons to buttons container...");
    buttons.appendChild(cancelButton);
    buttons.appendChild(confirmButton);

    // console.log("[LMCQ Prompt] Appending elements to content container...");
    contentContainer.appendChild(header);
    contentContainer.appendChild(identifierLabel);
    contentContainer.appendChild(identifierInput);
    contentContainer.appendChild(passwordLabel);
    contentContainer.appendChild(passwordInput);
    contentContainer.appendChild(machineCodeLabel);
    contentContainer.appendChild(machineCodeInput);
    contentContainer.appendChild(buttons);

    // Use app.ui.dialog.show() to display the content
    // console.log("[LMCQ Prompt] Calling app.ui.dialog.show() with content container...");
    try {
        app.ui.dialog.show(contentContainer);
        // console.log("[LMCQ Prompt] app.ui.dialog.show() called successfully.");
    } catch(e) {
         console.error("[LMCQ Prompt] Error calling app.ui.dialog.show():", e);
         alert("无法显示 ComfyUI 对话框，请检查控制台。");
         callback(null, null, null); // Ensure callback is called even on failure
         return; 
    }
    
    // Focus and listeners (Should still work within the dialog)
    // console.log("[LMCQ Prompt] Setting focus to identifier input.");
    identifierInput.focus();
    // console.log("[LMCQ Prompt] Adding keydown listeners.");
    identifierInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') passwordInput.focus(); });
    passwordInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') machineCodeInput.focus(); });
    machineCodeInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) confirmButton.click(); });
    // console.log("[LMCQ Prompt] showGroupNodeSettingsPrompt function finished setup.");
}
// --- End Prompt ---

// Encipher function updated to send identifier and machine codes, expect only encrypted_text
async function encipher(subgraphJson, password, identifier, machineCodes) {
    try {
        // console.log(`[LMCQ GroupNode JS] Calling backend API /lmcq/encipher_group for identifier: ${identifier}`);
        const response = await api.fetchApi("/" + serverName + "/" + apiEndpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                "subgraph_json": subgraphJson,
                "password": password,
                "identifier": identifier, // Send identifier
                "machine_codes": machineCodes // Send machine codes list
             }),
        });

        let text = await response.text();
        let data = JSON.parse(text);

        if (response.status === 200 && data.success) {
            // Expecting only encrypted_text now
            if (!data.encrypted_text) {
                 throw new Error("服务器响应缺少必要数据 (encrypted_text)");
            }
            // console.log(`[LMCQ GroupNode JS] Received encrypted text for identifier: ${identifier}`);
            return { encryptedText: data.encrypted_text }; // Return only encryptedText
        } else {
            const errorMsg = data.msg || `HTTP Error ${response.status}: ${response.statusText}`;
            throw new Error(errorMsg);
        }
    } catch (error) {
        console.error("[LMCQ GroupNode JS] encipher error:", error);
        alert(`加密失败: ${error.message}`);
        throw error;
    }
}

// 检测是否会形成循环依赖的函数
function detectCycleInSelection(selectedNodes) {
    const selectedNodeIds = new Set(selectedNodes.map(node => String(node.id)));
    const graph = app.graph;
    
    // console.log(`[LMCQ GroupNode JS] Checking for potential cycles in selection:`, Array.from(selectedNodeIds));
    
    // 检查是否存在 A -> B -> C 的情况，其中 A 和 C 都在选择中，但 B 不在
    for (const nodeA of selectedNodes) {
        // 遍历 A 的所有输出连接
        if (nodeA.outputs) {
            for (let outputSlot = 0; outputSlot < nodeA.outputs.length; outputSlot++) {
                const output = nodeA.outputs[outputSlot];
                if (output.links) {
                    for (const linkId of output.links) {
                        const link = graph.links[linkId];
                        if (link) {
                            const nodeB = graph._nodes_by_id[link.target_id];
                            // 如果 B 不在选择中
                            if (nodeB && !selectedNodeIds.has(String(nodeB.id))) {
                                // 检查 B 的输出是否连接到选择中的其他节点
                                if (nodeB.outputs) {
                                    for (let bOutputSlot = 0; bOutputSlot < nodeB.outputs.length; bOutputSlot++) {
                                        const bOutput = nodeB.outputs[bOutputSlot];
                                        if (bOutput.links) {
                                            for (const bLinkId of bOutput.links) {
                                                const bLink = graph.links[bLinkId];
                                                if (bLink) {
                                                    const nodeC = graph._nodes_by_id[bLink.target_id];
                                                    // 如果 C 在选择中，就形成了 A -> B -> C 的循环风险
                                                    if (nodeC && selectedNodeIds.has(String(nodeC.id))) {
                                                        return {
                                                            hasLoop: true,
                                                            nodeA: nodeA,
                                                            nodeB: nodeB,
                                                            nodeC: nodeC,
                                                            message: `检测到潜在循环：节点"${nodeA.title || nodeA.type}"和"${nodeC.title || nodeC.type}"通过中间节点"${nodeB.title || nodeB.type}"相连。将它们加密到同一组会形成循环依赖。`
                                                        };
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    return { hasLoop: false };
}

// Updated function to use ComfyUI's standard graphToPrompt API for reliable connection analysis
async function addEncryptedGroupNode(selected, identifier, password, machineCodes) {
    const selectedNodeIds = selected.map(node => String(node.id));
    const graph = app.graph;
    
    // console.log(`[LMCQ GroupNode JS] Starting group creation for ${selectedNodeIds.length} nodes using ComfyUI standard API`);
    // console.log(`[LMCQ GroupNode JS] Selected node IDs:`, selectedNodeIds);
    
    // --- 🚨 预检测循环依赖 ---
    const cycleCheck = detectCycleInSelection(selected);
    if (cycleCheck.hasLoop) {
        alert(`❌ 无法创建加密组：\n\n${cycleCheck.message}\n\n建议解决方案：\n1. 分别加密这些节点\n2. 或者同时选择中间节点"${cycleCheck.nodeB.title || cycleCheck.nodeB.type}"`);
        console.error(`[LMCQ GroupNode JS] Cycle detected, aborting group creation`);
        return null;
    }
    
    // --- 🚀 使用ComfyUI标准API获取连接信息 ---
    const promptData = await app.graphToPrompt();
    const output = promptData.output;
    
    // console.log(`[LMCQ GroupNode JS] Got prompt data with ${Object.keys(output).length} nodes`);
    
    // --- 📊 分析跨组边界的连接 ---
    const externalInputs = new Map(); // 需要创建的输入端口
    const externalOutputs = new Map(); // 需要创建的输出端口
    const internalSubgraph = {}; // 内部子图数据
    
    // 1. 直接分析选中节点的输入端口连接（更准确的方法）
    for (const nodeId of selectedNodeIds) {
        const node = graph._nodes_by_id[nodeId];
        if (node) {
            // 先从prompt.output获取节点基础数据（如果存在）
            if (output[nodeId]) {
                internalSubgraph[nodeId] = { ...output[nodeId], outputs: [] };
            } else {
                // 如果prompt.output中没有，创建基础结构
                console.warn(`[LMCQ GroupNode JS] Node ${nodeId} not found in prompt.output, creating basic structure`);
                internalSubgraph[nodeId] = { 
                    inputs: {}, 
                    class_type: node.comfyClass || node.type,
                    outputs: [] 
                };
                
                // 添加widget数据
                if (node.widgets) {
                    for (const widget of node.widgets) {
                    if (!widget.options || widget.options.serialize !== false) {
                            internalSubgraph[nodeId].inputs[widget.name] = widget.serializeValue ? 
                                await widget.serializeValue(node, widget) : widget.value;
                    }
                }
            }
            }
            
            console.log(`[LMCQ GroupNode JS] Analyzing inputs for internal node: ${nodeId} (${node.inputs?.length || 0} inputs)`);
            
            // 直接分析节点的输入端口连接
            if (node.inputs) {
                for (let inputSlot = 0; inputSlot < node.inputs.length; inputSlot++) {
                    const inputPort = node.inputs[inputSlot];
                    const inputName = inputPort.name;
                    
                    console.log(`[LMCQ GroupNode JS] Checking input ${nodeId}:${inputSlot} (${inputName}), link: ${inputPort.link}`);
                    
                    if (inputPort.link !== null && inputPort.link !== undefined) {
                        const link = graph.links[inputPort.link];
                        if (link && !selectedNodeIds.includes(String(link.origin_id))) {
                            // 这是一个来自外部的输入连接
                            const sourceNode = graph._nodes_by_id[link.origin_id];
                            if (sourceNode && sourceNode.outputs && sourceNode.outputs[link.origin_slot]) {
                                const sourceOutput = sourceNode.outputs[link.origin_slot];
                                const inputKey = `${nodeId}:${inputName}`;
                                
                                externalInputs.set(inputKey, {
                                    sourceNodeId: String(link.origin_id),
                                    sourceSlot: link.origin_slot,
                                    targetNodeId: nodeId,
                                    inputName: inputName,
                                    inputType: sourceOutput.type,
                                    sourceNode: sourceNode,
                                    targetNode: node,
                                    targetSlot: inputSlot
                                });
                                
                                console.log(`[LMCQ GroupNode JS] ✅ External input found: ${link.origin_id}:${link.origin_slot} (${sourceOutput.name}) -> ${nodeId}:${inputSlot} (${inputName}) [${sourceOutput.type}]`);
                            }
                        } else if (link) {
                            console.log(`[LMCQ GroupNode JS] Internal connection: ${link.origin_id}:${link.origin_slot} -> ${nodeId}:${inputSlot}`);
                        }
                    } else {
                        console.log(`[LMCQ GroupNode JS] Input ${nodeId}:${inputSlot} (${inputName}) has no connection`);
                    }
                }
            }
        }
    }
    
    // 2. 直接分析选中节点的输出端口连接（更准确的方法）
    for (const nodeId of selectedNodeIds) {
        const node = graph._nodes_by_id[nodeId];
        if (node && node.outputs) {
            console.log(`[LMCQ GroupNode JS] Analyzing outputs for internal node: ${nodeId} (${node.outputs.length} outputs)`);
            
            for (let outputSlot = 0; outputSlot < node.outputs.length; outputSlot++) {
                const outputPort = node.outputs[outputSlot];
                const outputKey = `${nodeId}:${outputSlot}`;
                
                console.log(`[LMCQ GroupNode JS] Checking output ${outputKey}: ${outputPort.name} (${outputPort.type}), links: ${outputPort.links?.length || 0}`);
                
                // 检查这个输出是否连接到外部节点
                if (outputPort.links && outputPort.links.length > 0) {
                    for (const linkId of outputPort.links) {
                        const link = graph.links[linkId];
                        if (link && !selectedNodeIds.includes(String(link.target_id))) {
                            // 这个输出连接到了外部节点
                            const targetNode = graph._nodes_by_id[link.target_id];
                            if (targetNode && targetNode.inputs && targetNode.inputs[link.target_slot]) {
                                const targetInput = targetNode.inputs[link.target_slot];
                                
                                externalOutputs.set(outputKey, {
                                    sourceNodeId: nodeId,
                                    sourceSlot: outputSlot,
                                    targetNodeId: String(link.target_id),
                                    inputName: targetInput.name,
                                    outputType: outputPort.type,
                                    outputName: outputPort.name,
                                    sourceNode: node,
                                    targetNode: targetNode,
                                    targetSlot: link.target_slot
                                });
                                
                                // console.log(`[LMCQ GroupNode JS] ✅ External output found: ${nodeId}:${outputSlot} (${outputPort.name}) -> ${link.target_id}:${link.target_slot} (${targetInput.name})`);
                                break; // 只需要记录一次这个输出端口
                            }
                        }
                    }
                } else {
                    console.log(`[LMCQ GroupNode JS] Output ${outputKey} has no external connections`);
                }
            }
        }
    }
    
    // console.log(`[LMCQ GroupNode JS] Analysis complete: ${externalInputs.size} external inputs, ${externalOutputs.size} external outputs`);
    
    // --- 🏗️ 创建加密组节点 ---
    const encryptedGroupNode = LiteGraph.createNode(nodeName);
    encryptedGroupNode.removeOutput(0); // 移除默认输出
    encryptedGroupNode.pos = selected[0].pos;
    encryptedGroupNode.title = identifier;
    graph.add(encryptedGroupNode);
    
    // console.log(`[LMCQ GroupNode JS] Created encrypted group node: ${encryptedGroupNode.id}`);
    
    // --- 📥 创建输入端口并建立外部输入连接 ---
    const inputPortMapping = new Map();
    let inputPortIndex = 0;
    
        for (const [inputKey, inputInfo] of externalInputs) {
        try {
            const portName = `${inputInfo.inputName}_${inputPortIndex}`;
            encryptedGroupNode.addInput(portName, inputInfo.inputType);
            
            // 先断开原有连接
            inputInfo.targetNode.disconnectInput(inputInfo.targetSlot);
            
            // 建立从外部节点到组节点的连接
            inputInfo.sourceNode.connect(inputInfo.sourceSlot, encryptedGroupNode, inputPortIndex);
            
            // 更新内部子图数据，将外部输入映射到隐藏端口
            internalSubgraph[inputInfo.targetNodeId].inputs[inputInfo.inputName] = ["hidden", portName];
            
            inputPortMapping.set(inputKey, portName);
            
            // console.log(`[LMCQ GroupNode JS] ✅ Created input port ${inputPortIndex}: ${portName} (${inputInfo.inputType})`);
            // console.log(`[LMCQ GroupNode JS] ✅ Connected external input: ${inputInfo.sourceNodeId}:${inputInfo.sourceSlot} -> group:${inputPortIndex}`);
            
            inputPortIndex++;
        } catch (error) {
            console.error(`[LMCQ GroupNode JS] ❌ Failed to create input port for ${inputKey}:`, error);
        }
    }
    
    // --- 📤 创建输出端口并建立外部输出连接 ---
    const outputPortMapping = new Map();
    let outputPortIndex = 0;
    
    for (const [outputKey, outputInfo] of externalOutputs) {
        try {
            const portName = `${outputInfo.outputName}_${outputPortIndex}`;
            encryptedGroupNode.addOutput(portName, outputInfo.outputType);
            
            // 先断开原有连接
            outputInfo.targetNode.disconnectInput(outputInfo.targetSlot);
            
            // 建立新的连接：组节点输出 -> 外部节点输入
            encryptedGroupNode.connect(outputPortIndex, outputInfo.targetNode, outputInfo.targetSlot);
            
            outputPortMapping.set(outputKey, {
                portIndex: outputPortIndex,
                portName: portName,
                outputInfo: outputInfo
            });
            
            // console.log(`[LMCQ GroupNode JS] ✅ Created output port ${outputPortIndex}: ${portName} (${outputInfo.outputType})`);
            // console.log(`[LMCQ GroupNode JS] ✅ Connected external output: group:${outputPortIndex} -> ${outputInfo.targetNodeId}:${outputInfo.targetSlot} (${outputInfo.inputName})`);
            
            outputPortIndex++;
        } catch (error) {
            console.error(`[LMCQ GroupNode JS] ❌ Failed to create output port for ${outputKey}:`, error);
        }
    }
    
    // --- 📊 构建最终子图数据 ---
    const finalSubgraphData = {
        ...internalSubgraph
    };
    
        // --- 🔗 构建输出映射 ---
    const outputsMapping = [];
    for (const [outputKey, portMapping] of outputPortMapping) {
        const { portIndex } = portMapping;
        const [nodeId, outputSlot] = outputKey.split(':');
        
        // 输出映射格式：[组节点输出索引, 内部节点ID, 内部节点输出槽位]
        outputsMapping.push([portIndex, nodeId, parseInt(outputSlot)]);
        
        // console.log(`[LMCQ GroupNode JS] Output mapping: group port ${portIndex} <- internal ${nodeId}:${outputSlot}`);
    }
    
    // 设置输出映射到子图数据
    finalSubgraphData._outputs_ = outputsMapping;
    //
    
    // 🚨 重要：正确处理内部连接，保留原有的outputs数据
    for (const nodeId in finalSubgraphData) {
        if (nodeId === '_outputs_') continue; // 跳过特殊字段
        
        // 检查输入中是否有隐藏输入引用外部节点
        if (finalSubgraphData[nodeId].inputs) {
            for (const inputName in finalSubgraphData[nodeId].inputs) {
                const inputValue = finalSubgraphData[nodeId].inputs[inputName];
                
                // 如果输入值是数组且第一个元素是节点ID，检查是否为外部节点
                if (Array.isArray(inputValue) && inputValue.length >= 2) {
                    const [sourceNodeId, sourceSlot] = inputValue;
                    
                    // 如果引用的是外部节点，转换为隐藏输入
                    if (!selectedNodeIds.includes(String(sourceNodeId))) {
                        // 找到对应的输入端口映射
                        for (const [inputKey, portName] of inputPortMapping) {
                            if (inputKey === `${nodeId}:${inputName}`) {
                                finalSubgraphData[nodeId].inputs[inputName] = ["hidden", portName];
                                console.log(`[LMCQ GroupNode JS] Converted external reference to hidden input: ${inputName} -> ${portName}`);
                                break;
                            }
                        }
                    }
                }
            }
        }
        
        // 确保节点数据结构完整性
        if (!finalSubgraphData[nodeId].class_type) {
            console.warn(`[LMCQ GroupNode JS] ⚠️  Node ${nodeId} missing class_type, attempting to recover...`);
            const node = graph._nodes_by_id[nodeId];
            if (node) {
                finalSubgraphData[nodeId].class_type = node.comfyClass || node.type;
            }
        }
        
        // 🚨 清理outputs数组：保留内部连接，移除外部引用（防止循环依赖）
        if (finalSubgraphData[nodeId].outputs && Array.isArray(finalSubgraphData[nodeId].outputs)) {
            const originalOutputsCount = finalSubgraphData[nodeId].outputs.length;
            
            // 过滤outputs：只保留指向内部节点的连接
            finalSubgraphData[nodeId].outputs = finalSubgraphData[nodeId].outputs.filter(output => {
                if (Array.isArray(output) && output.length >= 2) {
                    const targetNodeId = String(output[1]); // 目标节点ID
                    const isInternal = selectedNodeIds.includes(targetNodeId);
                    
                    if (!isInternal) {
                        console.log(`[LMCQ GroupNode JS] Removed external output reference: ${nodeId} -> ${targetNodeId} (preventing cycle)`);
                }
                    
                    return isInternal; // 只保留内部连接
                }
                return false; // 移除格式不正确的条目
            });
            
            console.log(`[LMCQ GroupNode JS] Node ${nodeId} outputs cleaned: ${originalOutputsCount} -> ${finalSubgraphData[nodeId].outputs.length} (internal only)`);
        } else {
            // 确保outputs是数组格式
            finalSubgraphData[nodeId].outputs = [];
            console.log(`[LMCQ GroupNode JS] Node ${nodeId} outputs initialized as empty array`);
        }
    }
    
    // console.log(`[LMCQ GroupNode JS] Final subgraph data cleaned and prepared`);
    // console.log(`[LMCQ GroupNode JS] Internal nodes: ${Object.keys(finalSubgraphData).length}`);
    // console.log(`[LMCQ GroupNode JS] Created ${encryptedGroupNode.inputs?.length || 0} input ports and ${encryptedGroupNode.outputs?.length || 0} output ports`);
    
    try {
        // 加密子图数据
        const { encryptedText } = await encipher(JSON.stringify(finalSubgraphData, null, 2), password, identifier, machineCodes);
        
        // 设置加密数据
        const dataWidget = encryptedGroupNode.widgets?.find(w => w.name === "encrypted_subgraph");
        if (dataWidget) {
            dataWidget.value = encryptedText;
            // console.log("[LMCQ GroupNode JS] Set encrypted_subgraph widget value.");
        } else {
            throw new Error("内部错误：无法存储加密数据。");
        }

        // 设置标识符
        const identifierWidget = encryptedGroupNode.widgets?.find(w => w.name === "workflow_identifier");
        if (identifierWidget) {
            identifierWidget.value = identifier;
            if (identifierWidget.inputEl) {
                identifierWidget.inputEl.disabled = true;
            }
            // console.log("[LMCQ GroupNode JS] Set workflow_identifier widget value.");
        } else {
             throw new Error("内部错误：无法存储加密节点组名称。");
        }
        
        // 触发更新
        if (app.nodeOutputs) app.nodeOutputs.networkIO?.markDirty();
        encryptedGroupNode.setDirtyCanvas(true, false);
         
                // --- 🗑️ 安全删除原始节点 ---
        // console.log(`[LMCQ GroupNode JS] Removing ${selectedNodeIds.length} original nodes...`);
        
        for (let i = app.graph._nodes.length - 1; i >= 0; i--) {
            const node = app.graph._nodes[i];
            if (selectedNodeIds.includes(String(node.id))) {
                // console.log(`[LMCQ GroupNode JS] Removing node: ${node.id} (${node.title})`);
                
                try {
                    // 让ComfyUI的标准方法处理节点移除
                    if (node.onRemoved) {
                        node.onRemoved();
                    }
                    
                    // 从图中移除节点（LiteGraph会自动处理连接清理）
                    graph.remove(node);
                    
                } catch (error) {
                    console.warn(`[LMCQ GroupNode JS] Warning: Error removing node ${node.id}:`, error);
                    // 即使出错也继续，不中断整个过程
                }
            }
        }
        
        // 最终清理和重绘
        graph.setDirtyCanvas(true, true)
        
        // console.log("[LMCQ GroupNode JS] ✅ Node group creation completed successfully");
        return encryptedGroupNode;
        
    } catch (error) {
        console.error("[LMCQ GroupNode JS] ❌ addEncryptedGroupNode failed:", error);
        if (encryptedGroupNode.graph) { 
            graph.remove(encryptedGroupNode); 
        }
        throw error;
    }
}

// Register the node type
app.registerExtension({
    name: "Comfy.lmcq." + nodeName,
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === nodeName) {
            
            // --- Restore hideWidgetElement function (ensure it's robust) --- 
            const hideWidgetElement = (nodeInstance, widgetInstance) => {
                if (!widgetInstance || !nodeInstance) return;
                let widgetElement = widgetInstance.inputEl?.closest('.widget') || 
                                    widgetInstance.element?.closest('.widget') ||
                                    widgetInstance.canvas?.closest('.widget');   
                if (!widgetElement && widgetInstance.inputEl) widgetElement = widgetInstance.inputEl;
                if (!widgetElement && widgetInstance.element) widgetElement = widgetInstance.element;
                if (!widgetElement && widgetInstance.canvas) widgetElement = widgetInstance.canvas;
                
                if (widgetElement) {
                    if (widgetElement.style.display !== 'none' || !widgetElement.dataset.lmcqForcedHide) {
                        // console.log(`[LMCQ GroupNode] Force hiding widget: ${widgetInstance.name}`);
                        widgetElement.style.setProperty('display', 'none', 'important');
                        widgetElement.style.setProperty('visibility', 'hidden', 'important');
                        widgetElement.style.setProperty('position', 'absolute', 'important'); 
                        widgetElement.style.setProperty('top', '-9999px', 'important');
                        widgetElement.style.setProperty('left', '-9999px', 'important');
                        widgetElement.style.setProperty('width', '0px', 'important');
                        widgetElement.style.setProperty('height', '0px', 'important'); 
                        widgetElement.style.setProperty('margin', '0px', 'important');
                        widgetElement.style.setProperty('padding', '0px', 'important');
                        widgetElement.style.setProperty('overflow', 'hidden', 'important');
                        widgetElement.dataset.lmcqForcedHide = 'true';
                        if (!widgetInstance._hiddenSizeCalculated) {
                             nodeInstance.computeSize(); 
                             nodeInstance.setDirtyCanvas(true, false);
                             widgetInstance._hiddenSizeCalculated = true;
                        }
                    }
                } else {
                     if (!widgetInstance._warnedNotFound) {
                          console.warn(`[LMCQ GroupNode] Could not find DOM element for widget: ${widgetInstance.name} to hide.`);
                          widgetInstance._warnedNotFound = true;
                     }
                }
            };
            // --- END hideWidgetElement --- 
            
            // --- Restore hideTargetWidgets function --- 
            const hideTargetWidgets = (nodeInst) => {
                 if (!nodeInst || !nodeInst.widgets) return;
                 const dataWidget = nodeInst.widgets.find(w => w.name === "encrypted_subgraph");
                 const idWidget = nodeInst.widgets.find(w => w.name === "workflow_identifier");
                 if (dataWidget) hideWidgetElement(nodeInst, dataWidget);
                 if (idWidget) hideWidgetElement(nodeInst, idWidget);
             };
            // --- END hideTargetWidgets --- 

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // --- Initialize identifier widget: Disable, Override computeSize --- 
                try {
                    const idWidget = this.widgets ? this.widgets.find(w => w.name === "workflow_identifier") : null;
                    if (idWidget) {
                        // 1. Disable input
                        if (idWidget.inputEl) {
                            idWidget.inputEl.disabled = true;
                        } else {
                            setTimeout(() => { if (idWidget.inputEl) idWidget.inputEl.disabled = true; }, 50);
                        }
                        
                        // 2. Override computeSize for initial layout hint
                        idWidget.computeSize = () => [0, -4]; 
                        // console.log("[LMCQ GroupNode JS onNodeCreated] Overrode computeSize for workflow_identifier widget.");
                        
                        // 3. Potentially mark as not dirty (experimental)
                        // idWidget.dirty = false;
                        
                        // Initial hide call (might be redundant due to onDrawBackground but safe)
                        hideWidgetElement(this, idWidget);
                        
                        // No longer overriding draw here
                        // idWidget.draw = ... 

                        this.setDirtyCanvas(true, true); // Trigger redraw after computeSize override
                    } 
                } catch(e) {
                     console.error("[LMCQ GroupNode JS onNodeCreated] Error initializing identifier widget:", e);
                }
                // --- END Initialization ---

                // --- Serialize logic (unchanged) ---
                const originalSerialize = this.serialize;
                this.serialize = () => {
                    const data = originalSerialize.call(this);
                    if (data.widgets_values && Array.isArray(data.widgets_values)) {
                         // 查找由 Python 定义创建的密码小部件 (它应该是 widgets 数组中的第一个)
                         const passwordWidgetIndex = this.widgets ? this.widgets.findIndex(w => w.name === "password") : -1;
                         if (passwordWidgetIndex !== -1 && passwordWidgetIndex < data.widgets_values.length) {
                             console.log(`[LMCQ GroupNode Serialize] Clearing password widget at index ${passwordWidgetIndex}`);
                              data.widgets_values[passwordWidgetIndex] = "";
                         } else {
                             console.warn("[LMCQ GroupNode Serialize] Could not find password widget index in widgets_values to clear.");
                         }
                    }
                    return data;
                };

                // --- Configure logic (unchanged) ---
                const originalConfigure = this.configure;
                this.configure = (info) => {
                    originalConfigure.apply(this, [info]);

                    // --- 动态重建输入/输出端口 ---
                    if (info.inputs) {
                        for (const savedInput of info.inputs) {
                            // 检查实例上是否已存在同名输入 (configure 可能已部分创建)
                            const existingInput = this.inputs ? this.inputs.find(i => i.name === savedInput.name) : null;
                            if (!existingInput) {
                                // console.log(`[LMCQ GroupNode Configure] Adding missing input: ${savedInput.name} (${savedInput.type})`);
                                this.addInput(savedInput.name, savedInput.type);
                            }
                        }
                    }
                    if (info.outputs) {
                        for (const savedOutput of info.outputs) {
                            // 检查实例上是否已存在同名输出
                            const existingOutput = this.outputs ? this.outputs.find(o => o.name === savedOutput.name) : null;
                            if (!existingOutput) {
                                // console.log(`[LMCQ GroupNode Configure] Adding missing output: ${savedOutput.name} (${savedOutput.type})`);
                                this.addOutput(savedOutput.name, savedOutput.type);
                             }
                        }
                         // Ensure outputs list length matches info.outputs length if necessary
                         // (LiteGraph might handle this, but good to be aware)
                         if (this.outputs.length < info.outputs.length) {
                             console.warn("[LMCQ GroupNode Configure] Node outputs count mismatch after adding, might indicate deeper issue.");
                         }
                    }
                    // --- 结束端口重建 ---

                    // 清理密码小部件的值 (不变)
                    const passwordWidget = this.widgets ? this.widgets.find(w => w.name === "password") : null;
                    if (passwordWidget) {
                        passwordWidget.value = "";
                     }
                };

                return r;
            };

            // --- Restore onDrawBackground FOR PERSISTENT HIDING --- 
            const onDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                 onDrawBackground?.apply(this, arguments);
                 // Persistently hide the target widgets on every draw cycle
                 hideTargetWidgets(this); 
            };
            // --- End Restore --- 
        }
    },
});

// Function to add the right-click menu option (Updated)
function addConvertToEncryptedGroupOptions() {
    function addOption(options, index, selectedNodes) {
        let disabled = selectedNodes.length < 1;
        let menuText = menuLabel;
        
        if (selectedNodes.length > 0) {
            // 检查是否会形成循环
            const cycleCheck = detectCycleInSelection(selectedNodes);
            if (cycleCheck.hasLoop) {
                disabled = true;
                menuText = `❌ ${menuLabel} (已选 ${selectedNodes.length} 个，会形成死循环，请分开加密)`;
            } else {
                menuText = `${menuLabel} (已选 ${selectedNodes.length} 个)`;
            }
        }
        
        options.splice(index + 1, 0, { // Insert
            content: menuText,
            disabled,
            callback: async () => {
                 // --- ADD LOGGING & TRY-CATCH ---
                 console.log("[LMCQ GroupNode JS] Menu option clicked. Trying to show prompt...");
                 try {
                     showGroupNodeSettingsPrompt((identifier, password, machineCodes) => { // Use renamed prompt
                         console.log("[LMCQ GroupNode JS] Prompt callback executed (identifier:", identifier, ")"); // Log callback execution
                         if (identifier !== null && password !== null) { // Check identifier and password
                             console.log("[LMCQ GroupNode JS] Prompt confirmed. Adding node...");
                             // Pass all collected data
                             addEncryptedGroupNode(selectedNodes, identifier, password, machineCodes);
                         } else {
                             console.log("[LMCQ GroupNode JS] Prompt cancelled or closed.");
                         }
                     });
                     // console.log("[LMCQ GroupNode JS] showGroupNodeSettingsPrompt function called successfully.");
                 } catch (e) {
                     console.error("[LMCQ GroupNode JS] Error occurred when trying to show/call prompt:", e);
                     alert("无法显示加密设置对话框，请检查浏览器控制台获取错误信息。");
                 }
                 // --- END LOGGING & TRY-CATCH ---
            },
        });
    }

    // --- Canvas Menu Options (Add Logging & Try-Catch) ---
    const origGetCanvasMenuOptions = LGraphCanvas.prototype.getCanvasMenuOptions;
    LGraphCanvas.prototype.getCanvasMenuOptions = function() {
        // console.log("[LMCQ GroupNode JS] getCanvasMenuOptions called."); // Log override trigger
        const options = origGetCanvasMenuOptions.apply(this, arguments);
        const selectedNodes = Object.values(app.canvas.selected_nodes || {});
        const group = this.graph.getGroupOnPos(this.graph_mouse[0], this.graph_mouse[1]);

        if (group) {
            const nodesInGroup = group._nodes;
            let disabled = !nodesInGroup || nodesInGroup.length < 1;
            let groupMenuText = `${menuLabel} (组: ${group.title})`;
            
            if (nodesInGroup && nodesInGroup.length > 0) {
                // 检查组中的节点是否会形成循环
                const cycleCheck = detectCycleInSelection(nodesInGroup);
                if (cycleCheck.hasLoop) {
                    disabled = true;
                    groupMenuText = `❌ ${menuLabel} (组: ${group.title}, 会形成死循环，请分开加密)`;
                }
            }
            
            options.push({
                content: groupMenuText,
                disabled,
                callback: async () => {
                    // --- ADD LOGGING & TRY-CATCH ---
                    // console.log("[LMCQ GroupNode JS] Group menu option clicked. Trying to show prompt...");
                    try {
                        showGroupNodeSettingsPrompt((identifier, password, machineCodes) => {
                            // console.log("[LMCQ GroupNode JS] Group prompt callback executed (identifier:", identifier, ")");
                            if (identifier !== null && password !== null) {
                                console.log("[LMCQ GroupNode JS] Group prompt confirmed. Adding node...");
                                addEncryptedGroupNode(nodesInGroup, identifier, password, machineCodes);
                            } else {
                                console.log("[LMCQ GroupNode JS] Group prompt cancelled or closed.");
                            }
                        });
                        // console.log("[LMCQ GroupNode JS] showGroupNodeSettingsPrompt (for group) called successfully.");
                     } catch (e) {
                         console.error("[LMCQ GroupNode JS] Error occurred when trying to show/call group prompt:", e);
                         alert("无法显示组加密设置对话框，请检查浏览器控制台获取错误信息。");
                     }
                     // --- END LOGGING & TRY-CATCH ---
                }
            });
        }

        // Add to canvas right-click menu
        if (typeof addOption === 'function') {
             console.log("[LMCQ GroupNode JS] Adding option to canvas menu.");
             addOption(options, options.length, selectedNodes);
        } else {
             console.error("[LMCQ GroupNode JS] addOption function is not defined in getCanvasMenuOptions!");
        }

        return options;
    };

    // --- Node Menu Options (Add Logging) ---
    const getNodeMenuOptions = LGraphCanvas.prototype.getNodeMenuOptions;
    LGraphCanvas.prototype.getNodeMenuOptions = function(node) {
        console.log("[LMCQ GroupNode JS] getNodeMenuOptions called for node:", node?.title);
        const options = getNodeMenuOptions.apply(this, arguments);
         const selectedNodes = Object.values(app.canvas.selected_nodes || {});

        if (selectedNodes.includes(node)) {
            const index = options.findIndex((o) => o?.content === "Remove") || options.length -1;
            if (typeof addOption === 'function') {
                 console.log("[LMCQ GroupNode JS] Adding option to node menu.");
                 addOption(options, index, selectedNodes);
            } else {
                 console.error("[LMCQ GroupNode JS] addOption function is not defined in getNodeMenuOptions!");
            }
         }

        return options;
    };
}

// Setup the extension
const id = "Lmcq." + nodeName;
const ext = {
    name: id,
    setup() {
        addConvertToEncryptedGroupOptions();
        console.log(`[LMCQ] 注册了 ${nodeName} 扩展。`);
    },
};

app.registerExtension(ext); 

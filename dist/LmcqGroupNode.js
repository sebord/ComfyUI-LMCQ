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
    console.log("[LMCQ Prompt] Created buttons and attached onclick handlers.");

    // Append elements to the content container
    console.log("[LMCQ Prompt] Appending buttons to buttons container...");
    buttons.appendChild(cancelButton);
    buttons.appendChild(confirmButton);

    console.log("[LMCQ Prompt] Appending elements to content container...");
    contentContainer.appendChild(header);
    contentContainer.appendChild(identifierLabel);
    contentContainer.appendChild(identifierInput);
    contentContainer.appendChild(passwordLabel);
    contentContainer.appendChild(passwordInput);
    contentContainer.appendChild(machineCodeLabel);
    contentContainer.appendChild(machineCodeInput);
    contentContainer.appendChild(buttons);

    // Use app.ui.dialog.show() to display the content
    console.log("[LMCQ Prompt] Calling app.ui.dialog.show() with content container...");
    try {
        app.ui.dialog.show(contentContainer);
        console.log("[LMCQ Prompt] app.ui.dialog.show() called successfully.");
    } catch(e) {
         console.error("[LMCQ Prompt] Error calling app.ui.dialog.show():", e);
         alert("无法显示 ComfyUI 对话框，请检查控制台。");
         callback(null, null, null); // Ensure callback is called even on failure
         return; 
    }
    
    // Focus and listeners (Should still work within the dialog)
    console.log("[LMCQ Prompt] Setting focus to identifier input.");
    identifierInput.focus();
    console.log("[LMCQ Prompt] Adding keydown listeners.");
    identifierInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') passwordInput.focus(); });
    passwordInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') machineCodeInput.focus(); });
    machineCodeInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) confirmButton.click(); });
    console.log("[LMCQ Prompt] showGroupNodeSettingsPrompt function finished setup.");
}
// --- End Prompt ---

// Encipher function updated to send identifier and machine codes, expect only encrypted_text
async function encipher(subgraphJson, password, identifier, machineCodes) {
    try {
        console.log(`[LMCQ GroupNode JS] Calling backend API /lmcq/encipher_group for identifier: ${identifier}`);
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
            console.log(`[LMCQ GroupNode JS] Received encrypted text for identifier: ${identifier}`);
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

// Updated function to pass identifier and machine codes, set identifier widget
async function addEncryptedGroupNode(selected, identifier, password, machineCodes) {
    const idList = selected.map(w => {
        return '' + w.id; // Get selected node IDs
    });

    const graph = app.graph;
    const promptData = await app.graphToPrompt();
    const workflow = promptData.workflow;
    const output = {};
    const otherOutput = {};
    let allInputs = [];
    
    for (const outerNode of graph.computeExecutionOrder(false)) {
        const skipNode = outerNode.mode === 2 || outerNode.mode === 4;
        const innerNodes = !skipNode && outerNode["getInnerNodes"] ? outerNode["getInnerNodes"]() : [outerNode];
        
        for (const node3 of innerNodes) {
            if (node3.isVirtualNode && idList.indexOf(node3.id + '') >= 0) {
                continue;
        }
            if (node3.mode === 2 || node3.mode === 4) {
                continue;
        }
            
            const inputs = {};
            const widgets = node3.widgets;
            if (widgets) {
                for (const i2 in widgets) {
                    const widget = widgets[i2];
                    if (!widget.options || widget.options.serialize !== false) {
                        inputs[widget.name] = widget.serializeValue ? await widget.serializeValue(node3, i2) : widget.value;
                    }
                }
            }
            
            for (let i2 in node3.inputs) {
                let parent = node3.getInputNode(i2);
                if (parent) {
                    let link = node3.getInputLink(i2);
                    while (parent.mode === 4 || parent.isVirtualNode) {
                        let found = false;
                        if (parent.isVirtualNode && idList.indexOf(parent.id + '') >= 0) {
                            link = parent.getInputLink(link.origin_slot);
                            if (link) {
                                parent = parent.getInputNode(link.target_slot);
                                if (parent) {
                                    found = true;
                                }
                            }
                        } else if (link && parent.mode === 4) {
                            let all_inputs = [link.origin_slot];
                            if (parent.inputs) {
                                all_inputs = all_inputs.concat(Object.keys(parent.inputs));
                                for (let parent_input in all_inputs) {
                                    parent_input = all_inputs[parent_input];
                                    if (parent.inputs[parent_input]?.type === node3.inputs[i2].type) {
                                        link = parent.getInputLink(parent_input);
                        if (link) {
                                            parent = parent.getInputNode(parent_input);
                                        }
                                        found = true;
                                        break;
                                    }
                                }
                            }
                        }
                        if (!found) {
                            break;
                        }
                    }
                    if (link) {
                        if (parent?.updateLink) {
                            link = parent.updateLink(link);
                        }
                        if (link) {
                            inputs[node3.inputs[i2].name] = [
                                String(link.origin_id),
                                parseInt(link.origin_slot)
                            ];
                            allInputs.push(link.origin_id + ":" + link.origin_slot);
                        }
                    }
                }
            }
            
            let node_data = {
                inputs,
                class_type: node3.comfyClass
            };
            
            if (app.ui.settings.getSettingValue("Comfy.DevMode")) {
                node_data["_meta"] = {
                    title: node3.title
                };
            }
            
            if (idList.indexOf(node3.id + '') >= 0 || idList.indexOf(outerNode.id + '') >= 0) {
                if (idList.indexOf(node3.id + '') < 0) {
                    idList.push(node3.id + '');
                }
                output[String(node3.id)] = node_data;
            } else {
                otherOutput[String(node3.id)] = node_data;
            }
        }
    }
    
    const encryptedGroupNode = LiteGraph.createNode(nodeName);
    encryptedGroupNode.removeOutput(0);
    encryptedGroupNode.pos = selected[0].pos;
    encryptedGroupNode.title = identifier; // Set node title to the identifier
    graph.add(encryptedGroupNode);
    
    let inputOriginIds = {};
    let inputOutputIds = {};
    
    for (const key in output) {
        output[key]['outputs'] = [];
        const node_data = output[key];
        let node = graph._nodes_by_id[key];
        const ids = key.split(':');
        if (!node && ids.length == 2) {
            node = graph._nodes_by_id[ids[0]].getInnerNodes()[parseInt(ids[1])];
        }
        
        if (node && 'inputs' in node)
            for (let j = 0; j < node.inputs.length; j++) {
                const link = node.inputs[j].link;
                const name = node.inputs[j].name;
                const type = node.inputs[j].type;
                if (name in node_data['inputs']) {
                    if (node_data['inputs'][name].length == 2 && idList.indexOf(node_data['inputs'][name][0]) < 0) {
                        let node_IDA = node_data['inputs'][name][0];
                        let origin_slotA = node_data['inputs'][name][1];
                        const IDAids = node_IDA.split(':');
                        if (IDAids.length == 2) {
                            node_IDA = graph.links[link].origin_id;
                            origin_slotA = graph.links[link].origin_slot;
                }
                        if ((node_IDA + ':' + origin_slotA) in inputOriginIds) {
                            output[key]["inputs"][name] = ["hidden", inputOriginIds[(node_IDA + ':' + origin_slotA)]];
                        } else {
                            encryptedGroupNode.addInput(name + "_" + ('inputs' in encryptedGroupNode ? encryptedGroupNode.inputs.length : 0), type);
                            const nName = encryptedGroupNode.inputs[encryptedGroupNode.inputs.length - 1].name;
                            output[key]["inputs"][name] = ["hidden", nName];
                            const connectedNodeA = graph._nodes_by_id[node_IDA];
                            try {
                                connectedNodeA.connect(origin_slotA, encryptedGroupNode, encryptedGroupNode.inputs.length - 1);
                                //node.disconnectInput(j)
                            } catch (error) {
                                console.error(error);
                            }
                            inputOriginIds[(node_IDA + ':' + origin_slotA)] = nName;
                        }
                    }
            } else {
                    encryptedGroupNode.addInput(name + "_" + ('inputs' in encryptedGroupNode ? encryptedGroupNode.inputs.length : 0), type);
                    const nName = encryptedGroupNode.inputs[encryptedGroupNode.inputs.length - 1].name;
                    output[key]["inputs"][name] = ["hidden", nName];
            }
            }
        
        if (node && 'outputs' in node)
            for (let j = 0; j < node.outputs.length; j++) {
                const linkAs = node.outputs[j].links;
                const name = node.outputs[j].name;
                const type = node.outputs[j].type;
                if (!(linkAs && linkAs.length > 0) && allInputs.indexOf(node.id + ':' + j) < 0) {
                    encryptedGroupNode.addOutput(name + "_" + ('outputs' in encryptedGroupNode ? encryptedGroupNode.outputs.length : 0), type);
                    output[key]['outputs'].push([encryptedGroupNode.outputs.length - 1, j]);
                    inputOutputIds[key + ':' + j] = [encryptedGroupNode.outputs.length - 1, j];
                }
            }
        }
    
    for (const key in otherOutput) {
        const node_data = otherOutput[key];
        const node = graph._nodes_by_id[key];
        if (node && 'inputs' in node)
            for (let j = 0; j < node.inputs.length; j++) {
                const link = node.inputs[j].link;
                const name = node.inputs[j].name;
                const type = node.inputs[j].type;
                if (link && name in node_data['inputs'] && idList.indexOf(node_data['inputs'][name][0]) >= 0) {
                    const node_IDA = node_data['inputs'][name][0];
                    const origin_slotA = node_data['inputs'][name][1];
                    if ((node_IDA + ':' + origin_slotA) in inputOutputIds) {
                        output[node_IDA]["outputs"].push(inputOutputIds[(node_IDA + ':' + origin_slotA)]);
                    } else {
                        const inode = graph._nodes_by_id[node_IDA];
                        const { name, type } = inode.outputs[origin_slotA];
                        encryptedGroupNode.addOutput(name + "_" + ('outputs' in encryptedGroupNode ? encryptedGroupNode.outputs.length : 0), type);
                        node.disconnectInput(j);
                        inputOutputIds[(node_IDA + ':' + origin_slotA)] = [encryptedGroupNode.outputs.length - 1, origin_slotA];
                        output[node_IDA]["outputs"].push([encryptedGroupNode.outputs.length - 1, origin_slotA]);
                        encryptedGroupNode.connect(encryptedGroupNode.outputs.length - 1, node, j);
                }
            }
        }
    }

    console.log("[LMCQ GroupNode JS] Subgraph structure prepared:", output);

    // --- Construct final subgraph data (unchanged) ---
    const finalSubgraphData = {
        ...output,
        _outputs_: []
    };
    
    // 填充输出映射
    for (const internalNodeOutputKey in inputOutputIds) {
        // internalNodeOutputKey 格式是 "node_id:slot_index"
        const [internalNodeId, internalSlotIndexStr] = internalNodeOutputKey.split(':');
        const internalSlotIndex = parseInt(internalSlotIndexStr);
        const [groupOutputIndex, _] = inputOutputIds[internalNodeOutputKey]; // 我们只需要组的输出索引
        finalSubgraphData._outputs_.push([groupOutputIndex, internalNodeId, internalSlotIndex]);
    }
    // --- End construct ---
    
    try {
        // Pass identifier and machineCodes to encipher, receive only encryptedText
        const { encryptedText } = await encipher(JSON.stringify(finalSubgraphData, null, 2), password, identifier, machineCodes);
        
        // --- Set widget value for encrypted_subgraph (Remains) ---
        const dataWidget = encryptedGroupNode.widgets ? encryptedGroupNode.widgets.find(w => w.name === "encrypted_subgraph") : null;
        if (dataWidget) {
            dataWidget.value = encryptedText;
            console.log("[LMCQ GroupNode JS] Set encrypted_subgraph widget value.");
        } else {
            console.error("[LMCQ GroupNode JS] Error: Could not find 'encrypted_subgraph' widget to store data!");
            throw new Error("内部错误：无法存储加密数据。");
        }

        // --- REINSTATE Setting workflow_identifier WIDGET value --- 
        const identifierWidget = encryptedGroupNode.widgets ? encryptedGroupNode.widgets.find(w => w.name === "workflow_identifier") : null;
        if (identifierWidget) {
            identifierWidget.value = identifier; // Set value from prompt
            console.log("[LMCQ GroupNode JS] Set workflow_identifier widget value.");
            // REINSTATE disabling
            if (identifierWidget.inputEl) {
                identifierWidget.inputEl.disabled = true;
                console.log("[LMCQ GroupNode JS] Disabled workflow_identifier input.");
            } else {
                 console.warn("[LMCQ GroupNode JS] Could not find inputEl for workflow_identifier to disable immediately after creation.");
            }
        } else {
             console.error("[LMCQ GroupNode JS] Error: Could not find 'workflow_identifier' widget to store ID!");
             throw new Error("内部错误：无法存储加密节点组名称。");
        }
        // --- End REINSTATE ---
        
        // Trigger update
        if (app.nodeOutputs) app.nodeOutputs.networkIO?.markDirty();
        encryptedGroupNode.setDirtyCanvas(true, false);
         
        // Delete original nodes
        for (let e = app.graph._nodes.length - 1; 0 <= e; e--) {
            var a = app.graph._nodes[e];
            if (idList.indexOf(a.id + '') >= 0) {
                app.graph._nodes[e].onRemoved && app.graph._nodes[e].onRemoved();
                app.graph._nodes.splice(e, 1);
             }
         }

        return encryptedGroupNode;
    } catch (error) {
        console.error("[LMCQ GroupNode JS] addEncryptedGroupNode failed:", error);
        if (encryptedGroupNode.graph) { graph.remove(encryptedGroupNode); }
        return null;
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
                        console.log("[LMCQ GroupNode JS onNodeCreated] Overrode computeSize for workflow_identifier widget.");
                        
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
                                console.log(`[LMCQ GroupNode Configure] Adding missing input: ${savedInput.name} (${savedInput.type})`);
                                this.addInput(savedInput.name, savedInput.type);
                            }
                        }
                    }
                    if (info.outputs) {
                        for (const savedOutput of info.outputs) {
                            // 检查实例上是否已存在同名输出
                            const existingOutput = this.outputs ? this.outputs.find(o => o.name === savedOutput.name) : null;
                            if (!existingOutput) {
                                console.log(`[LMCQ GroupNode Configure] Adding missing output: ${savedOutput.name} (${savedOutput.type})`);
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
        const disabled = selectedNodes.length < 1;
        options.splice(index + 1, 0, { // Insert
            content: menuLabel + (selectedNodes.length > 0 ? ` (已选 ${selectedNodes.length} 个)` : ""),
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
                     console.log("[LMCQ GroupNode JS] showGroupNodeSettingsPrompt function called successfully.");
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
        console.log("[LMCQ GroupNode JS] getCanvasMenuOptions called."); // Log override trigger
        const options = origGetCanvasMenuOptions.apply(this, arguments);
        const selectedNodes = Object.values(app.canvas.selected_nodes || {});
        const group = this.graph.getGroupOnPos(this.graph_mouse[0], this.graph_mouse[1]);

        if (group) {
            const nodesInGroup = group._nodes;
            const disabled = !nodesInGroup || nodesInGroup.length < 1;
            options.push({
                content: `${menuLabel} (组: ${group.title})`,
                disabled,
                callback: async () => {
                    // --- ADD LOGGING & TRY-CATCH ---
                    console.log("[LMCQ GroupNode JS] Group menu option clicked. Trying to show prompt...");
                    try {
                        showGroupNodeSettingsPrompt((identifier, password, machineCodes) => {
                            console.log("[LMCQ GroupNode JS] Group prompt callback executed (identifier:", identifier, ")");
                            if (identifier !== null && password !== null) {
                                console.log("[LMCQ GroupNode JS] Group prompt confirmed. Adding node...");
                                addEncryptedGroupNode(nodesInGroup, identifier, password, machineCodes);
                            } else {
                                console.log("[LMCQ GroupNode JS] Group prompt cancelled or closed.");
                            }
                        });
                        console.log("[LMCQ GroupNode JS] showGroupNodeSettingsPrompt (for group) called successfully.");
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
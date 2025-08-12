import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";
import { $el } from "/scripts/ui.js"; // Use ComfyUI's standard element creation

// Use LMCQ specific names
const nodeName = "LmcqGroupNode";
const serverName = "lmcq";
const apiEndpoint = "encipher_group";
const menuLabel = "LMCQ-云加密组"; // Label remains

// 密码持久化相关函数
const LMCQ_PASSWORD_STORAGE_KEY = 'lmcq_group_node_passwords';
const LMCQ_LICENSE_CODE_STORAGE_KEY = 'lmcq_group_node_license_codes';

// 保存密码到localStorage
function savePasswordToStorage(nodeId, password) {
    try {
        // ✅ 增加输入验证
        if (!nodeId || typeof nodeId !== 'string' && typeof nodeId !== 'number') {
            console.warn('[LMCQ Password] Invalid nodeId for password storage:', nodeId);
            return;
        }
        
        const storedPasswords = JSON.parse(localStorage.getItem(LMCQ_PASSWORD_STORAGE_KEY) || '{}');
        storedPasswords[String(nodeId)] = password;
        localStorage.setItem(LMCQ_PASSWORD_STORAGE_KEY, JSON.stringify(storedPasswords));
        console.log(`[LMCQ Password] Saved password for node ${nodeId}`);
    } catch (error) {
        console.warn('[LMCQ Password] Failed to save password to localStorage:', error);
    }
}

// 保存授权码到localStorage
function saveLicenseCodeToStorage(nodeId, licenseCode) {
    try {
        if (!nodeId || typeof nodeId !== 'string' && typeof nodeId !== 'number') {
            console.warn('[LMCQ LicenseCode] Invalid nodeId for license code storage:', nodeId);
            return;
        }
        
        const storedLicenseCodes = JSON.parse(localStorage.getItem(LMCQ_LICENSE_CODE_STORAGE_KEY) || '{}');
        storedLicenseCodes[String(nodeId)] = licenseCode;
        localStorage.setItem(LMCQ_LICENSE_CODE_STORAGE_KEY, JSON.stringify(storedLicenseCodes));
        console.log(`[LMCQ LicenseCode] Saved license code for node ${nodeId}`);
    } catch (error) {
        console.warn('[LMCQ LicenseCode] Failed to save license code to localStorage:', error);
    }
}

// 从localStorage获取密码
function getPasswordFromStorage(nodeId) {
    try {
        // ✅ 增加输入验证
        if (!nodeId || typeof nodeId !== 'string' && typeof nodeId !== 'number') {
            console.warn('[LMCQ Password] Invalid nodeId for password retrieval:', nodeId);
            return '';
        }
        
        const storedPasswords = JSON.parse(localStorage.getItem(LMCQ_PASSWORD_STORAGE_KEY) || '{}');
        return storedPasswords[String(nodeId)] || '';
    } catch (error) {
        console.warn('[LMCQ Password] Failed to retrieve password from localStorage:', error);
        return '';
    }
}

// 从localStorage获取授权码
function getLicenseCodeFromStorage(nodeId) {
    try {
        if (!nodeId || typeof nodeId !== 'string' && typeof nodeId !== 'number') {
            console.warn('[LMCQ LicenseCode] Invalid nodeId for license code retrieval:', nodeId);
            return '';
        }
        
        const storedLicenseCodes = JSON.parse(localStorage.getItem(LMCQ_LICENSE_CODE_STORAGE_KEY) || '{}');
        return storedLicenseCodes[String(nodeId)] || '';
    } catch (error) {
        console.warn('[LMCQ LicenseCode] Failed to retrieve license code from localStorage:', error);
        return '';
    }
}

// 从localStorage删除密码
function removePasswordFromStorage(nodeId) {
    try {
        // ✅ 增加输入验证
        if (!nodeId || typeof nodeId !== 'string' && typeof nodeId !== 'number') {
            console.warn('[LMCQ Password] Invalid nodeId for password removal:', nodeId);
            return;
        }
        
        const storedPasswords = JSON.parse(localStorage.getItem(LMCQ_PASSWORD_STORAGE_KEY) || '{}');
        delete storedPasswords[String(nodeId)];
        localStorage.setItem(LMCQ_PASSWORD_STORAGE_KEY, JSON.stringify(storedPasswords));
        console.log(`[LMCQ Password] Removed password for node ${nodeId}`);
    } catch (error) {
        console.warn('[LMCQ Password] Failed to remove password from localStorage:', error);
    }
}

// 从localStorage删除授权码
function removeLicenseCodeFromStorage(nodeId) {
    try {
        if (!nodeId || typeof nodeId !== 'string' && typeof nodeId !== 'number') {
            console.warn('[LMCQ LicenseCode] Invalid nodeId for license code removal:', nodeId);
            return;
        }
        
        const storedLicenseCodes = JSON.parse(localStorage.getItem(LMCQ_LICENSE_CODE_STORAGE_KEY) || '{}');
        delete storedLicenseCodes[String(nodeId)];
        localStorage.setItem(LMCQ_LICENSE_CODE_STORAGE_KEY, JSON.stringify(storedLicenseCodes));
        console.log(`[LMCQ LicenseCode] Removed license code for node ${nodeId}`);
    } catch (error) {
        console.warn('[LMCQ LicenseCode] Failed to remove license code from localStorage:', error);
    }
}

// 清理不存在的节点的密码
function cleanupStoredPasswords() {
    try {
        const storedPasswords = JSON.parse(localStorage.getItem(LMCQ_PASSWORD_STORAGE_KEY) || '{}');
        const storedLicenseCodes = JSON.parse(localStorage.getItem(LMCQ_LICENSE_CODE_STORAGE_KEY) || '{}');
        const currentNodeIds = new Set();
        
        // 收集当前所有LmcqGroupNode的ID - 增加安全检查
        if (app.graph && app.graph._nodes && Array.isArray(app.graph._nodes)) {
            for (const node of app.graph._nodes) {
                // ✅ 增加安全检查：确保节点对象存在且有有效的id和type
                if (node && 
                    typeof node === 'object' && 
                    node.id !== undefined && 
                    node.id !== null && 
                    node.type === nodeName) {
                    currentNodeIds.add(String(node.id));
                }
            }
        }
        
        // 删除不存在的节点的密码和授权码
        let hasPasswordChanges = false;
        let hasLicenseCodeChanges = false;
        
        for (const nodeId in storedPasswords) {
            if (!currentNodeIds.has(nodeId)) {
                delete storedPasswords[nodeId];
                hasPasswordChanges = true;
                console.log(`[LMCQ Password] Cleaned up password for removed node ${nodeId}`);
            }
        }
        
        for (const nodeId in storedLicenseCodes) {
            if (!currentNodeIds.has(nodeId)) {
                delete storedLicenseCodes[nodeId];
                hasLicenseCodeChanges = true;
                console.log(`[LMCQ LicenseCode] Cleaned up license code for removed node ${nodeId}`);
            }
        }
        
        if (hasPasswordChanges) {
            localStorage.setItem(LMCQ_PASSWORD_STORAGE_KEY, JSON.stringify(storedPasswords));
        }
        
        if (hasLicenseCodeChanges) {
            localStorage.setItem(LMCQ_LICENSE_CODE_STORAGE_KEY, JSON.stringify(storedLicenseCodes));
        }
    } catch (error) {
        console.warn('[LMCQ Password] Failed to cleanup stored passwords:', error);
    }
}

// ✅ 新增：安全的密码清理函数，专门用于工作流切换后
function safeCleanupStoredPasswords() {
    // 检查应用状态是否准备就绪
    if (!app || !app.graph || !app.canvas) {
        console.log('[LMCQ Password] App not ready for password cleanup, skipping...');
        return;
    }
    
    // 延迟执行，确保工作流完全加载完成
    setTimeout(() => {
        cleanupStoredPasswords();
    }, 2000); // 增加延迟时间
}

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

// Updated function (legacy) removed to avoid duplicate identifier; kept newer implementation below.

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
                    // Password widget - 实现密码持久化
                    const passwordWidget = this.widgets?.find(w => w.name === "password");
                    if (passwordWidget) {
                        const nodeId = String(this.id);
                        
                        // 恢复保存的密码
                        const savedPassword = getPasswordFromStorage(nodeId);
                        if (savedPassword) {
                            passwordWidget.value = savedPassword;
                            console.log(`[LMCQ Password] Restored password for node ${nodeId}`);
                        }
                        
                        // 保存原始callback
                        const originalCallback = passwordWidget.callback;
                        
                        // 重写callback以实现自动保存
                        passwordWidget.callback = (value) => {
                            // 先调用原始callback
                            if (originalCallback) {
                                originalCallback.call(passwordWidget, value);
                            }
                            
                            // 保存密码到localStorage
                            if (value && value.trim()) {
                                savePasswordToStorage(nodeId, value);
                            } else {
                                // 如果密码为空，从存储中删除
                                removePasswordFromStorage(nodeId);
                            }
                        };
                        
                        // 为输入框添加change和blur事件监听（如果有输入框）
                        if (passwordWidget.inputEl) {
                            const handlePasswordChange = () => {
                                const value = passwordWidget.inputEl.value;
                                passwordWidget.value = value; // 更新widget值
                                if (value && value.trim()) {
                                    savePasswordToStorage(nodeId, value);
                                } else {
                                    removePasswordFromStorage(nodeId);
                                }
                            };
                            
                            passwordWidget.inputEl.addEventListener('input', handlePasswordChange);
                            passwordWidget.inputEl.addEventListener('change', handlePasswordChange);
                            passwordWidget.inputEl.addEventListener('blur', handlePasswordChange);
                        } else {
                            // 如果输入框还没创建，稍后再试
                            setTimeout(() => {
                                if (passwordWidget.inputEl) {
                                    const handlePasswordChange = () => {
                                        const value = passwordWidget.inputEl.value;
                                        passwordWidget.value = value;
                                        if (value && value.trim()) {
                                            savePasswordToStorage(nodeId, value);
                                        } else {
                                            removePasswordFromStorage(nodeId);
                                        }
                                    };
                                    
                                    passwordWidget.inputEl.addEventListener('input', handlePasswordChange);
                                    passwordWidget.inputEl.addEventListener('change', handlePasswordChange);
                                    passwordWidget.inputEl.addEventListener('blur', handlePasswordChange);
                                }
                            }, 100);
                        }
                        
                        console.log(`[LMCQ Password] Initialized password persistence for node ${nodeId}`);
                    }
                    
                    // License Code widget - 实现授权码持久化
                    const licenseCodeWidget = this.widgets?.find(w => w.name === "license_code");
                    if (licenseCodeWidget) {
                        const nodeId = String(this.id);
                        
                        // 恢复保存的授权码
                        const savedLicenseCode = getLicenseCodeFromStorage(nodeId);
                        if (savedLicenseCode) {
                            licenseCodeWidget.value = savedLicenseCode;
                            console.log(`[LMCQ LicenseCode] Restored license code for node ${nodeId}`);
                        }
                        
                        // 保存原始callback
                        const originalLicenseCallback = licenseCodeWidget.callback;
                        
                        // 重写callback以实现自动保存
                        licenseCodeWidget.callback = (value) => {
                            // 先调用原始callback
                            if (originalLicenseCallback) {
                                originalLicenseCallback.call(licenseCodeWidget, value);
                            }
                            
                            // 保存授权码到localStorage
                            if (value && value.trim()) {
                                saveLicenseCodeToStorage(nodeId, value);
                            } else {
                                // 如果授权码为空，从存储中删除
                                removeLicenseCodeFromStorage(nodeId);
                            }
                        };
                        
                        // 为输入框添加change和blur事件监听（如果有输入框）
                        if (licenseCodeWidget.inputEl) {
                            const handleLicenseCodeChange = () => {
                                const value = licenseCodeWidget.inputEl.value;
                                licenseCodeWidget.value = value; // 更新widget值
                                if (value && value.trim()) {
                                    saveLicenseCodeToStorage(nodeId, value);
                                } else {
                                    removeLicenseCodeFromStorage(nodeId);
                                }
                            };
                            
                            licenseCodeWidget.inputEl.addEventListener('input', handleLicenseCodeChange);
                            licenseCodeWidget.inputEl.addEventListener('change', handleLicenseCodeChange);
                            licenseCodeWidget.inputEl.addEventListener('blur', handleLicenseCodeChange);
                        } else {
                            // 如果输入框还没创建，稍后再试
                            setTimeout(() => {
                                if (licenseCodeWidget.inputEl) {
                                    const handleLicenseCodeChange = () => {
                                        const value = licenseCodeWidget.inputEl.value;
                                        licenseCodeWidget.value = value;
                                        if (value && value.trim()) {
                                            saveLicenseCodeToStorage(nodeId, value);
                                        } else {
                                            removeLicenseCodeFromStorage(nodeId);
                                        }
                                    };
                                    
                                    licenseCodeWidget.inputEl.addEventListener('input', handleLicenseCodeChange);
                                    licenseCodeWidget.inputEl.addEventListener('change', handleLicenseCodeChange);
                                    licenseCodeWidget.inputEl.addEventListener('blur', handleLicenseCodeChange);
                                }
                            }, 100);
                        }
                        
                        console.log(`[LMCQ LicenseCode] Initialized license code persistence for node ${nodeId}`);
                    }
                    
                } catch(e) {
                     console.error("[LMCQ GroupNode JS onNodeCreated] Error initializing widgets:", e);
                }
                // --- END Initialization ---

                // --- Serialize logic - 清空工作流中的密码和授权码但保持localStorage ---
                const originalSerialize = this.serialize;
                this.serialize = () => {
                    const data = originalSerialize.call(this);
                    if (data.widgets_values && Array.isArray(data.widgets_values)) {
                         // 查找由 Python 定义创建的密码小部件
                         const passwordWidgetIndex = this.widgets ? this.widgets.findIndex(w => w.name === "password") : -1;
                         if (passwordWidgetIndex !== -1 && passwordWidgetIndex < data.widgets_values.length) {
                             // 保存当前密码到localStorage（以防还没保存）
                             const currentPassword = data.widgets_values[passwordWidgetIndex];
                             if (currentPassword && currentPassword.trim()) {
                                 savePasswordToStorage(String(this.id), currentPassword);
                             }
                             
                             console.log(`[LMCQ GroupNode Serialize] Clearing password from workflow at index ${passwordWidgetIndex}, but keeping in localStorage`);
                              data.widgets_values[passwordWidgetIndex] = "";
                         } else {
                             console.warn("[LMCQ GroupNode Serialize] Could not find password widget index in widgets_values to clear.");
                         }
                         
                         // 查找由 Python 定义创建的授权码小部件
                         const licenseCodeWidgetIndex = this.widgets ? this.widgets.findIndex(w => w.name === "license_code") : -1;
                         if (licenseCodeWidgetIndex !== -1 && licenseCodeWidgetIndex < data.widgets_values.length) {
                             // 保存当前授权码到localStorage（以防还没保存）
                             const currentLicenseCode = data.widgets_values[licenseCodeWidgetIndex];
                             if (currentLicenseCode && currentLicenseCode.trim()) {
                                 saveLicenseCodeToStorage(String(this.id), currentLicenseCode);
                             }
                             
                             console.log(`[LMCQ GroupNode Serialize] Clearing license code from workflow at index ${licenseCodeWidgetIndex}, but keeping in localStorage`);
                              data.widgets_values[licenseCodeWidgetIndex] = "";
                         } else {
                             console.warn("[LMCQ GroupNode Serialize] Could not find license code widget index in widgets_values to clear.");
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

                    // 恢复密码小部件的值 (而不是清空) - 增加安全检查
                    const passwordWidget = this.widgets ? this.widgets.find(w => w.name === "password") : null;
                    if (passwordWidget && this && this.id !== undefined && this.id !== null) {
                        const nodeId = String(this.id);
                        const savedPassword = getPasswordFromStorage(nodeId);
                        if (savedPassword) {
                            passwordWidget.value = savedPassword;
                            console.log(`[LMCQ Password] Restored password in configure for node ${nodeId}`);
                        }
                    } else if (!passwordWidget) {
                        console.log('[LMCQ Password] No password widget found for password restoration');
                    } else {
                        console.warn('[LMCQ Password] Cannot restore password: node or node.id is undefined');
                    }
                    
                    // 恢复授权码小部件的值 - 增加安全检查
                    const licenseCodeWidget = this.widgets ? this.widgets.find(w => w.name === "license_code") : null;
                    if (licenseCodeWidget && this && this.id !== undefined && this.id !== null) {
                        const nodeId = String(this.id);
                        const savedLicenseCode = getLicenseCodeFromStorage(nodeId);
                        if (savedLicenseCode) {
                            licenseCodeWidget.value = savedLicenseCode;
                            console.log(`[LMCQ LicenseCode] Restored license code in configure for node ${nodeId}`);
                        }
                    } else if (!licenseCodeWidget) {
                        console.log('[LMCQ LicenseCode] No license code widget found for license code restoration');
                    } else {
                        console.warn('[LMCQ LicenseCode] Cannot restore license code: node or node.id is undefined');
                    }
                };

                return r;
            };

            // 添加onRemoved回调以清理密码和授权码存储
            const onRemoved = nodeType.prototype.onRemoved;
            nodeType.prototype.onRemoved = function() {
                // ✅ 增加安全检查
                if (this && this.id !== undefined && this.id !== null) {
                    const nodeId = String(this.id);
                    removePasswordFromStorage(nodeId);
                    removeLicenseCodeFromStorage(nodeId);
                    console.log(`[LMCQ Password] Cleaned up password and license code for removed node ${nodeId}`);
                } else {
                    console.warn('[LMCQ Password] Cannot clean up password and license code: node or node.id is undefined');
                }
                
                if (onRemoved) {
                    return onRemoved.apply(this, arguments);
                }
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
    // Idempotent install guard to avoid duplicate menu entries
    try {
        if (typeof LGraphCanvas === 'undefined') return;
        const proto = LGraphCanvas.prototype;
        if (proto.__lmcq_menu_patched__) return;
        // mark as patched at the end after successful overrides
    } catch (e) {
        // If environment not ready, just return silently
        return;
    }
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
    if (!LGraphCanvas.prototype.__lmcq_canvas_menu_wrapped__) {
    LGraphCanvas.prototype.getCanvasMenuOptions = function() {
        // console.log("[LMCQ GroupNode JS] getCanvasMenuOptions called."); // Log override trigger
        const options = origGetCanvasMenuOptions ? origGetCanvasMenuOptions.apply(this, arguments) : [];
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
    LGraphCanvas.prototype.__lmcq_canvas_menu_wrapped__ = true;
    }

    // --- Node Menu Options (Add Logging) ---
    const getNodeMenuOptions = LGraphCanvas.prototype.getNodeMenuOptions;
    if (!LGraphCanvas.prototype.__lmcq_node_menu_wrapped__) {
    LGraphCanvas.prototype.getNodeMenuOptions = function(node) {
        console.log("[LMCQ GroupNode JS] getNodeMenuOptions called for node:", node?.title);
        const options = getNodeMenuOptions.apply(this, arguments);
         const selectedNodes = Object.values(app.canvas.selected_nodes || {});

        // Always append our option; disabled state is handled inside addOption
        const index = options.length - 1;
            if (typeof addOption === 'function') {
                 console.log("[LMCQ GroupNode JS] Adding option to node menu.");
                 addOption(options, index, selectedNodes);
            } else {
                 console.error("[LMCQ GroupNode JS] addOption function is not defined in getNodeMenuOptions!");
         }

        return options;
    };
    LGraphCanvas.prototype.__lmcq_node_menu_wrapped__ = true;
    }

    // Set patched flag
    try { LGraphCanvas.prototype.__lmcq_menu_patched__ = true; } catch (e) {}
}

// Setup the extension
const id = "Lmcq." + nodeName;
const ext = {
    name: id,
    setup() {
        addConvertToEncryptedGroupOptions();
        
        // ✅ 使用安全的密码清理函数
        safeCleanupStoredPasswords();
        
        console.log(`[LMCQ] 注册了 ${nodeName} 扩展，密码和授权码持久化系统已初始化。`);
        console.log(`[LMCQ] 可在控制台使用 window.clearLmcqPasswords() 清除所有保存的密码和授权码`);
    },
    
    // ✅ 新增：监听工作流加载事件
    async loadedGraphNode(node, app) {
        // 当节点加载完成时，进行安全的密码清理
        if (node.type === nodeName) {
            console.log(`[LMCQ Password] ${nodeName} node loaded, scheduling password cleanup...`);
            // 延迟执行，确保所有节点都已加载
            setTimeout(() => {
                safeCleanupStoredPasswords();
            }, 500);
        }
    },
    
    // ✅ 新增：工作流改变时的处理（确保菜单挂载）
    async graphChanged(graph) {
        console.log('[LMCQ Password] Graph changed, scheduling password cleanup...');
        safeCleanupStoredPasswords();
        // 重新挂载一次右键菜单，以兼容某些场景下 Canvas 菜单被重置
        addConvertToEncryptedGroupOptions();
    }
};

// 提供全局函数用于清除所有保存的密码
window.clearLmcqPasswords = function() {
    try {
        localStorage.removeItem(LMCQ_PASSWORD_STORAGE_KEY);
        localStorage.removeItem(LMCQ_LICENSE_CODE_STORAGE_KEY);
        console.log('[LMCQ Password] All saved passwords and license codes have been cleared');
        alert('所有保存的LMCQ加密组密码和授权码已清除');
    } catch (error) {
        console.error('[LMCQ Password] Failed to clear passwords:', error);
        alert('清除密码失败，请检查控制台');
    }
};

app.registerExtension(ext); 

// ===== LMCQ Encrypted Group: Subgraph-like merge and auto-rewire (refactor) =====
// NOTE: We purposely avoid touching any cloud API flow on the backend. This client-side
// logic builds the subgraph JSON, requests encryption, creates a group node, rewires
// external links automatically, and injects a hidden widget (kwargsObj) that serializes
// upstream link tuples for backend expansion.

// Try installing context menus as early as possible (in case other extensions override later)
try {
    // In some load orders, app.registerExtension may be too late to attach menus
    // We proactively call the installer once here; the real hook still exists above
    if (typeof LGraphCanvas !== 'undefined') {
        // re-attach canvas/node menu overrides safely
        addConvertToEncryptedGroupOptions();
        console.log('[LMCQ GroupNode JS] Early menu attach');
    }
} catch (e) {
    // ignore
}

// Build a unique, stable id for nodes within the selection (string)
function stableId(node) {
    return String(node.id);
}

// Build external input/output exposure for selected nodes
async function analyzeSelection(selection) {
    const selected = new Set(selection.map(n => n.id));
    const graph = app.graph;

    const innerNodes = selection;
    const subgraphNodes = {}; // id -> { class_type, inputs }

    // Exposed inputs/outputs metadata for the group node UI
    const exposedInputs = [];  // [{ name, type }]
    const exposedOutputs = []; // [{ name, type, innerNodeId, innerSlot }]

    // For rewiring later
    const externalInputLinks = [];  // [{ inputName, innerNodeId, innerSlot, origin_id, origin_slot }]
    const externalOutputLinks = []; // [{ groupOutputIndex, innerNodeId, innerSlot, target_id, target_slot }]

    // Helper: get slot name/type safely
    function getInputSlotInfo(node, slotIndex) {
        const slot = node.inputs?.[slotIndex];
        return {
            name: slot?.name ?? `in_${slotIndex}`,
            type: slot?.type ?? "*"
        };
    }
    function getOutputSlotInfo(node, slotIndex) {
        const slot = node.outputs?.[slotIndex];
        return {
            name: slot?.name ?? `out_${slotIndex}`,
            type: slot?.type ?? "*"
        };
    }

    // Map from exposed output to group output index for deterministic order
    let groupOutputCounter = 0;

    // Dedup map for external inputs by source (origin node + slot)
    const inputBySource = new Map(); // key -> { name, type }

    function allocateExposedInputName(baseName) {
        let name = baseName || 'input';
        const used = new Set(exposedInputs.map(e => e.name));
        if (!used.has(name)) return name;
        let i = 1;
        while (used.has(`${name}_${i}`)) i++;
        return `${name}_${i}`;
    }

    for (const node of innerNodes) {
        const id = stableId(node);
        const class_type = node.comfyClass || node.type;
        const inputs = {};

        // Inputs: internal vs external
        for (let i = 0; i < (node.inputs?.length || 0); i++) {
            const linkId = node.inputs[i]?.link;
            if (linkId == null) continue;
            const link = graph.links[linkId];
            if (!link) continue;

            const origin_id = String(link.origin_id);
            const origin_slot = link.origin_slot;
            const isInternal = selected.has(link.origin_id);
            const { name: inputName } = getInputSlotInfo(node, i);

            if (isInternal) {
                // link to another node within selection
                inputs[inputName] = [String(link.origin_id), origin_slot];
            } else {
                // external input -> deduplicate by source (origin_id, origin_slot)
                const srcKey = `${origin_id}:${origin_slot}`;
                let entry = inputBySource.get(srcKey);
                if (!entry) {
                    const base = inputName === 'clip' ? 'clip' : inputName || `in_${i}`;
                    const name = allocateExposedInputName(base);
                    const type = getInputSlotInfo(node, i).type;
                    entry = { name, type };
                    inputBySource.set(srcKey, entry);
                    exposedInputs.push({ name, type });
                }
                inputs[inputName] = ["hidden", entry.name];
                externalInputLinks.push({ inputName: entry.name, innerNodeId: id, innerSlot: i, origin_id, origin_slot });
            }
        }

        // Literal widget values
        if (node.widgets && node.widgets.length) {
            for (const w of node.widgets) {
                if (!w.name) continue;
                if (w.options?.serialize === false) continue;
                // Arrays need wrapping to avoid misinterpretation as links by backend
                const idx = node.widgets.indexOf(w);
                const v = w.serializeValue ? await w.serializeValue(node, idx) : w.value;
                if (inputs[w.name] == null) {
                    inputs[w.name] = Array.isArray(v) ? { __value__: v } : v;
                }
            }
        }

        subgraphNodes[id] = { class_type, inputs };

        // Outputs: any links to outside selection become group outputs
        for (let o = 0; o < (node.outputs?.length || 0); o++) {
            const olinks = node.outputs[o]?.links || [];
            for (const l of olinks) {
                const link = graph.links[l];
                if (!link) continue;
                if (selected.has(link.target_id)) continue; // internal
                const { name: outName, type } = getOutputSlotInfo(node, o);
                const exposedName = `${node.title || node.type}_${outName}`;
                let groupOutputIndex = exposedOutputs.findIndex(e => e.innerNodeId === id && e.innerSlot === o);
                if (groupOutputIndex === -1) {
                    groupOutputIndex = exposedOutputs.length;
                    exposedOutputs.push({ name: exposedName, type, innerNodeId: id, innerSlot: o });
                }
                externalOutputLinks.push({ groupOutputIndex, innerNodeId: id, innerSlot: o, target_id: String(link.target_id), target_slot: link.target_slot });
            }
        }
    }

    // Build _outputs_ mapping for backend result ordering
    const outputsMapping = exposedOutputs.map((e, idx) => [idx, e.innerNodeId, e.innerSlot]);

    return {
        subgraphNodes,
        exposedInputs,
        exposedOutputs,
        outputsMapping,
        externalInputLinks,
        externalOutputLinks
    };
}

async function requestEncryptSubgraph({ subgraph_json, password, identifier, machineCodes }) {
    const body = {
        subgraph_json: JSON.stringify(subgraph_json),
        password,
        identifier,
        machine_codes: machineCodes || []
    };
    const resp = await api.fetchApi(`/lmcq/encipher_group`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(`加密失败: ${txt}`);
    }
    const data = await resp.json();
    if (!data?.success) throw new Error(data?.msg || '加密失败');
    return data.encrypted_text;
}

// Hidden widget that serializes upstream links into kwargsObj for backend
function ensureKwargsWidget(node, exposedInputs) {
    node.widgets = node.widgets || [];
    const existing = node.widgets.find(w => w.name === 'kwargsObj');
    if (existing) return;
    const widget = {
        name: 'kwargsObj',
        type: 'OBJECT',
        options: { serialize: true },
        serializeValue: (n) => {
            const mapping = {};
            for (let i = 0; i < (n.inputs?.length || 0); i++) {
                const slot = n.inputs[i];
                const inputName = slot?.name;
                if (!inputName) continue;
                const linkId = slot?.link;
                if (linkId == null) continue;
                const link = app.graph.links[linkId];
                if (!link) continue;
                mapping[inputName] = [String(link.origin_id), link.origin_slot];
            }
            return mapping;
        },
        value: {}
    };
    node.widgets.push(widget);
}

function placeNodeAtSelection(node, selection) {
    let top, left;
    for (const n of selection) {
        if (left == null || n.pos[0] < left) left = n.pos[0];
        if (top == null || n.pos[1] < top) top = n.pos[1];
    }
    node.pos = [left ?? 100, top ?? 100];
}

function rewireCanvasForGroup(groupNode, selection, analysis) {
    const graph = app.graph;
    // Input rewiring: external origin -> groupNode input
    for (const e of analysis.externalInputLinks) {
        const originNode = graph.getNodeById(parseInt(e.origin_id));
        if (!originNode) continue;
        const groupInputIndex = groupNode.inputs.findIndex(inp => inp.name === e.inputName);
        if (groupInputIndex >= 0) {
            originNode.connect(e.origin_slot, groupNode, groupInputIndex);
        }
    }
    // Output rewiring: groupNode output -> external target
    for (const e of analysis.externalOutputLinks) {
        const targetNode = graph.getNodeById(parseInt(e.target_id));
        if (!targetNode) continue;
        const groupOutputIndex = e.groupOutputIndex;
        groupNode.connect(groupOutputIndex, targetNode, e.target_slot);
    }
}

async function addEncryptedGroupNode(selectedNodes, identifier, password, machineCodes) {
    const analysis = await analyzeSelection(selectedNodes);

    const subgraph_json = {
        ...analysis.subgraphNodes,
        _outputs_: analysis.outputsMapping
    };

    const encrypted_text = await requestEncryptSubgraph({ subgraph_json, password, identifier, machineCodes });

    // Create the group node instance (backend class LmcqGroupNodes)
    const group = LiteGraph.createNode('LmcqGroupNode');
    if (!group) throw new Error('无法创建 LmcqGroupNodes 节点');
    app.graph.add(group);

    // Remove any default outputs (e.g., wildcard "*") before adding exposed outputs
    if (group.outputs && group.outputs.length) {
        for (let i = group.outputs.length - 1; i >= 0; i--) {
            group.removeOutput(i);
        }
    }

    // Add exposed inputs/outputs
    for (const inp of analysis.exposedInputs) {
        group.addInput(inp.name, inp.type || "*");
    }
    for (const out of analysis.exposedOutputs) {
        group.addOutput(out.name, out.type || "*");
    }

    // Set widgets
    const setWidget = (name, value) => {
        const w = group.widgets?.find(w => w.name === name);
        if (w) w.value = value;
    };
    setWidget('password', password || '');
    setWidget('license_code', '');
    setWidget('encrypted_subgraph', encrypted_text);
    setWidget('workflow_identifier', identifier || '');

    // Hidden widget to serialize external links as kwargsObj
    ensureKwargsWidget(group, analysis.exposedInputs);

    // Prevent these visual inputs from being serialized as real backend inputs
    const originalGetInputLink = group.getInputLink?.bind(group);
    group.getInputLink = function(slot) {
        return null; // avoid executionUtil serializing link as node input
    };
    const originalGetInputNode = group.getInputNode?.bind(group);
    group.getInputNode = function(slot) {
        return null;
    };

    // Place group and rewire
    placeNodeAtSelection(group, selectedNodes);
    rewireCanvasForGroup(group, selectedNodes, analysis);

    // Remove original nodes
    for (const n of selectedNodes) app.graph.remove(n);

    // Force redraw
    app.graph.setDirtyCanvas(true, true);
}


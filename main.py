import gradio as gr
import requests

# 默认设置
templates = {
    "default_v0.0.3_extra": "你是“糖度计”AI，根据输入：\n- 若为食物名称，输出其Brix糖度，浮点数，精确到6位小数（如苹果：约10.000000-15.000000）。\n- 若为事件/任务/行为，根据知识评估其“唐”度（低能/离谱/令人恶心/尴尬程度），输出浮点数，范围[0.000000, 100.000000]，稍微随机一点，+-5%，严格符合事实，评价一般事物不要走极端。极少数超100表示极度离谱，精确到6位小数。\n仅输出浮点数，无其他内容。"
}
api_url = "https://api.openai.com/v1/chat/completions"
api_key = ""  # 请替换为您的API密钥
model_name = "gpt-4o-mini"

def query_model(food_name, template_name):
    """调用AI模型获取糖度值"""
    prompt = templates.get(template_name, templates["default_v0.0.3_extra"])
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model_name,
        "messages": [{"role": "system", "content": prompt},
                     {"role": "user", "content": food_name}]
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload)
        resp.raise_for_status() # 检查HTTP响应是否成功
        data = resp.json()
        raw_output = data["choices"][0]["message"]["content"].strip()
        val = float(raw_output)
    except Exception as e:
        return "0.0", "⚠️ 无法获取", f"错误: {e}"

    # 分类评语
    if val < 20.0:
        remark = "🟦 低糖"
    elif val < 60.0:
        remark = "🟩 中糖"
    elif val < 80.0:
        remark = "🟧 高糖"
    elif val <= 100.0:
        remark = "🟥 糖王"
    else:
        remark = "🌌 糖到没边"

    return str(val), remark, raw_output

def add_template(new_name, new_content):
    """添加新模版并同步更新两个下拉列表"""
    if new_name and new_content:
        templates[new_name] = new_content
        updated_keys = list(templates.keys())
        # 返回两个相同的列表，分别用于更新两个下拉菜单的 choices，
        # 并返回新添加的模版名称作为主页面的默认值，以避免错误。
        return updated_keys, gr.Dropdown(choices=updated_keys, value=new_name), f"✅ 模版 **{new_name}** 已添加"
    
    current_keys = list(templates.keys())
    # 如果添加失败，则返回当前列表并清空主页面的值以避免报错
    return current_keys, gr.Dropdown(choices=current_keys, value=current_keys[0]), "❌ 添加失败：名称或内容不能为空"

def update_settings(url, model, key):
    """更新API设置"""
    global api_url, model_name, api_key
    if url:
        api_url = url
    if model:
        model_name = model
    if key:
        api_key = key
    return f"✅ 已更新设置\nAPI URL: {api_url}\n模型: {model_name}"

with gr.Blocks(title="糖度计") as demo:
    gr.Markdown("# 🍬 糖度计")

    with gr.Tabs():
        with gr.Tab("检测"):
            food_input = gr.Textbox(label="输入食物名称")
            # 这里的 template_dropdown 将被 add_template 更新
            template_dropdown = gr.Dropdown(
                choices=list(templates.keys()), 
                value="default_v0.0.1_xafood", 
                label="模版选择"
            )
            btn = gr.Button("开始检测")
            with gr.Row():
                val_output = gr.Textbox(label="糖度值", lines=1, max_lines=1, interactive=False)
                remark_output = gr.Textbox(label="鉴定", lines=1, interactive=False)

            btn.click(
                fn=query_model, 
                inputs=[food_input, template_dropdown], 
                outputs=[val_output, remark_output]
            )

        with gr.Tab("模版管理"):
            new_name = gr.Textbox(label="新模版名称")
            new_content = gr.Textbox(label="新模版提示词", lines=5)
            add_btn = gr.Button("添加模版")
            # 这里的 template_list 将被 add_template 更新
            template_list = gr.Dropdown(
                choices=list(templates.keys()), 
                label="现有模版"
            )
            add_status = gr.Textbox(label="状态", interactive=False)

            add_btn.click(
                fn=add_template, 
                inputs=[new_name, new_content], 
                outputs=[template_list, template_dropdown, add_status]
            )
        
        with gr.Tab("高级设置"):
            api_url_in = gr.Textbox(label="API URL", value=api_url)
            model_in = gr.Textbox(label="模型名称", value=model_name)
            api_key_in = gr.Textbox(label="API Key", type="password", value=api_key)
            update_btn = gr.Button("更新设置")
            update_status = gr.Textbox(label="状态", interactive=False)

            update_btn.click(
                fn=update_settings, 
                inputs=[api_url_in, model_in, api_key_in], 
                outputs=update_status
            )

if __name__ == "__main__":
    demo.launch()
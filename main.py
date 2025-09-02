import gradio as gr
import requests

# Default settings that will appear in the UI
DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"

templates = {
    "default_v0.0.3_extra": "你是“糖度计”AI，根据输入：\n- 若为食物名称，输出其Brix糖度，浮点数，精确到6位小数（如苹果：约10.000000-15.000000）。\n- 若为事件/任务/行为，根据知识评估其“唐”度（低能/离谱/令人恶心/尴尬程度），输出浮点数，范围[0.000000, 100.000000]，稍微随机一点，+-5%，严格符合事实，评价一般事物不要走极端。极少数超100表示极度离谱，精确到6位小数。\n仅输出浮点数，无其他内容。"
}

# The main function now accepts api_url and api_key as arguments
def query_model(food_name, template_name, api_url, api_key, model_name):
    """调用AI模型获取糖度值, 使用用户在UI中提供的凭证"""
    # Check if the user has provided the API URL and Key
    if not api_key or not api_key.startswith("sk-"):
        return "0.0", "⚠️ API Key 无效", "错误: 请在“高级设置”选项卡中输入有效的 OpenAI API Key。"
    if not api_url:
        return "0.0", "⚠️ API URL 不能为空", "错误: 请在“高级设置”选项卡中输入 API URL。"

    prompt = templates.get(template_name, templates["default_v0.0.3_extra"])
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model_name,
        "messages": [{"role": "system", "content": prompt},
                     {"role": "user", "content": food_name}]
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload)
        resp.raise_for_status() # Check for HTTP errors
        data = resp.json()
        raw_output = data["choices"][0]["message"]["content"].strip()
        
        # Try to parse ranges like "10.0-15.0"
        if '-' in raw_output:
            val = float(raw_output.split('-')[0])
        else:
            val = float(raw_output)

    except Exception as e:
        raw_output_info = ""
        if 'resp' in locals() and hasattr(resp, 'text'):
            raw_output_info = f" | 原始响应: {resp.text}"
        return "0.0", "⚠️ 无法获取", f"错误: {e}{raw_output_info}"

    # Grade the result
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
    
    return raw_output, remark, raw_output

def add_template(new_name, new_content):
    """Adds a new template and updates dropdowns"""
    if new_name and new_content:
        templates[new_name] = new_content
        updated_keys = list(templates.keys())
        return gr.Dropdown(choices=updated_keys), gr.Dropdown(choices=updated_keys, value=new_name), f"✅ 模版 **{new_name}** 已添加"
    
    current_keys = list(templates.keys())
    return gr.Dropdown(choices=current_keys), gr.Dropdown(choices=current_keys, value=current_keys[0]), "❌ 添加失败：名称或内容不能为空"

with gr.Blocks(title="糖度计") as demo:
    gr.Markdown("# 🍬 糖度计")

    with gr.Tabs():
        with gr.Tab("高级设置"):
            gr.Markdown("请在此处输入您的 API 凭证。凭证仅在您的浏览器和目标 API 之间传输，不会被存储。")
            api_url_in = gr.Textbox(label="API URL", value=DEFAULT_API_URL)
            model_in = gr.Textbox(label="模型名称", value=DEFAULT_MODEL)
            api_key_in = gr.Textbox(label="API Key", type="password")
        
        with gr.Tab("检测"):
            food_input = gr.Textbox(label="输入食物名称或事件")
            template_dropdown = gr.Dropdown(
                choices=list(templates.keys()), 
                value="default_v0.0.3_extra", 
                label="模版选择"
            )
            btn = gr.Button("开始检测")
            with gr.Row():
                val_output = gr.Textbox(label="糖度值", interactive=False)
                remark_output = gr.Textbox(label="鉴定", interactive=False)
            
            raw_output_debug = gr.Textbox(label="原始输出 (调试用)", interactive=False)
            
            # CRITICAL CHANGE: Pass the values from the "高级设置" tab as inputs to the function
            btn.click(
                fn=query_model, 
                inputs=[food_input, template_dropdown, api_url_in, api_key_in, model_in], 
                outputs=[val_output, remark_output, raw_output_debug]
            )

        with gr.Tab("模版管理"):
            new_name = gr.Textbox(label="新模版名称")
            new_content = gr.Textbox(label="新模版提示词", lines=5)
            add_btn = gr.Button("添加模版")
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

# As before, ensure the launch() command is removed or commented out for deployment.
# if __name__ == "__main__":
#     demo.launch()

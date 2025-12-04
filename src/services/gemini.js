import { GoogleGenAI } from "@google/genai";

// 注意：实际项目中不要在前端直接暴露 key，这里仅为演示
const apiKey = import.meta.env.VITE_GEMINI_API_KEY || ''; 
let ai = null;

if (apiKey) {
    ai = new GoogleGenAI({ apiKey });
}

export const generateDescription = async (draft, type) => {
  if (!ai) {
    console.warn("Gemini API Key missing");
    return draft + " (AI功能未配置，请检查 .env 文件)";
  }

  const model = "gemini-2.5-flash";
  const prompt = type === 'item' 
    ? `你是一个乐于助人的校园二手交易助手。请润色以下商品描述，使其对买家更具吸引力。保持简洁但有说服力。请用中文回答。输入: "${draft}"`
    : `你是一个乐于助人的任务发布助手。请润色以下跑腿任务描述，使其清晰、简洁且礼貌，方便跑腿者接单。请用中文回答。输入: "${draft}"`;

  try {
    const response = await ai.models.generateContent({
      model,
      contents: prompt,
    });
    return response.text().trim(); // 注意 genai SDK 的返回值处理
  } catch (error) {
    console.error("Gemini generation error:", error);
    return draft;
  }
};
import { GoogleGenAI } from "@google/genai";

const GEMINI_API_KEY = process.env.API_KEY || '';

// Initialize only if key is present, otherwise we will mock for demo purposes if key is missing in UI
let ai: GoogleGenAI | null = null;
if (GEMINI_API_KEY) {
  ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });
}

export const analyzeSkillCluster = async (skills: string[]): Promise<string> => {
  if (!ai) return "Simulated Analysis: API Key not found. \n\nBased on the input skills, this cluster represents a high-value digital transformation segment. Recommend upskilling in Cloud Architecture.";

  try {
    const model = 'gemini-2.5-flash';
    const prompt = `
      Act as a Chief HR Officer at Škoda Auto.
      Analyze the following skill cluster from our organizational genome: ${skills.join(', ')}.
      
      Provide a brief strategic assessment covering:
      1. The evolutionary stage (Emerging, Dominant, or Regressive).
      2. A "Mutation Risk" (likelihood of these skills becoming obsolete).
      3. One concrete training recommendation.
      
      Keep it under 100 words.
    `;

    const response = await ai.models.generateContent({
      model: model,
      contents: prompt,
    });

    return response.text || "Analysis failed to generate text.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "Error retrieving AI analysis. Please check API configuration.";
  }
};

export const getManagerInsight = async (query: string, contextData: string): Promise<string> => {
   if (!ai) return "Simulated Insight: By analyzing the team diversity matrix, we see a 40% overlap in core competencies. This suggests high redundancy but low innovation potential.";

   try {
    const model = 'gemini-2.5-flash';
    const prompt = `
      Context: You are "Skill DNA", an AI assistant for Škoda Auto managers.
      Data Context: ${contextData}
      
      User Query: ${query}
      
      Provide a data-driven, professional, yet innovative answer using biological metaphors (genome, mutation, DNA) where appropriate.
    `;

    const response = await ai.models.generateContent({
      model: model,
      contents: prompt,
    });

    return response.text || "No insight generated.";
   } catch (error) {
     console.error("Gemini Insight Error", error);
     return "AI Service unavailable.";
   }
}
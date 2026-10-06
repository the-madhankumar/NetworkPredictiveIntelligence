import client from "./api_setup";

export const getPredict = async (grid_id, as_of = null) => {
  try {
    const response = await client.post("network/predict-risk", {
      grid_id: Number(grid_id),
      as_of: as_of,
    });
    return response.data;
  } catch (error) {
    console.error("Failed to fetch summary:", error);
    console.error("Backend response:", error.response?.data);
    return {
      error: true,
      message: error.response?.data?.detail || error.message || "An error occurred",
    };
  }
};

export const getPredictionExplanation = async (predictionData) => {
  try {
    const response = await client.post("assistant/explain-prediction", {
      grid_id: Number(predictionData.grid_id),
      as_of: predictionData.as_of || new Date().toISOString(),
      risk_score: Number(predictionData.risk_score ?? 0),
      risk_level: String(predictionData.risk_level ?? "low"),
      model_version: String(predictionData.model_version ?? "v1.0"),
      explanation_note: predictionData.explanation_note || null,
    });
    return response.data;
  } catch (error) {
    console.error("Failed to fetch explanation:", error);
    throw new Error(
      error.response?.data?.detail || "Failed to fetch prediction explanation."
    );
  }
};
const API_BASE_URL = "http://127.0.0.1:8000";

async function handleResponse(response, fallbackMessage) {
  if (!response.ok) {
    let message = fallbackMessage;

    try {
      const data = await response.json();
      message = data.detail || fallbackMessage;
    } catch {
      // Keep fallbackMessage if the response is not JSON.
    }

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return response.json();
}


export async function createSession() {
    const response = await fetch(`${API_BASE_URL}/api/session`, {
        method: "POST", 
        headers: {
            "Content-Type": "application/json",
        },
    });

    return handleResponse(response, "Could not create a chat session.");
}


export async function getHistory(sessionId, token) {
  const response = await fetch(
    `${API_BASE_URL}/api/history/${encodeURIComponent(sessionId)}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  return handleResponse(response, "Could not load chat history.");
}


export async function sendChat({
  sessionId,
  token,
  query,
  language = "en",
}) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      session_id: sessionId,
      query,
      language,
    }),
  });

  return handleResponse(response, "Could not send your message.");
}


export async function streamChat({
  sessionId,
  token,
  query,
  language = "en",
  onChunk,
}) {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      session_id: sessionId,
      query,
      language,
    }),
  });

  if (!response.ok) {
    let message = "Could not stream your message.";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Keep fallback message.
    }

    throw new Error(message);
  }

  if (!response.body) {
    throw new Error("Streaming is not supported by this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { value, done } = await reader.read();

      if (done) {
        break;
      }

      const chunk = decoder.decode(value, {
        stream: true,
      });

      if (chunk) {
        onChunk(chunk);
      }
    }

    const finalChunk = decoder.decode();

    if (finalChunk) {
      onChunk(finalChunk);
    }
  } finally {
    reader.releaseLock();
  }
}
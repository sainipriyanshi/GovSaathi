import { useEffect, useRef, useState } from "react";
import Card from "react-bootstrap/Card";
import Container from "react-bootstrap/Container";

import ChatInput from "./components/ChatInput";
import MessageBubble from "./components/MessageBubble";

import { createSession, getHistory, sendChat } from "./services/api";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";

const SESSION_STORAGE_KEY = "govsaathi_session";

function App() {
  const [messages, setMessages] = useState([]);
  const [session, setSession] = useState(null);
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current) {
      return;
    }

    initializedRef.current = true;

    async function initializeChat() {
      try {
        setLoading(true);
        setError("");

        const storedSession = localStorage.getItem(SESSION_STORAGE_KEY);

        let activeSession;

        if (storedSession) {
          try {
            activeSession = JSON.parse(storedSession);
          } catch {
            localStorage.removeItem(SESSION_STORAGE_KEY);
          }
        }

        if (!activeSession?.session_id || !activeSession?.token) {
          activeSession = await createSession();

          localStorage.setItem(
            SESSION_STORAGE_KEY,
            JSON.stringify(activeSession),
          );
        }

        const history = await getHistory(
          activeSession.session_id,
          activeSession.token,
        );

        setSession(activeSession);
        setMessages(history.messages || []);
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }

    initializeChat();
  }, []);

  async function handleSend(trimmedQuery) {
    if (!session || sending) {
      return;
    }

    try {
      setSending(true);
      setError("");

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `user-${Date.now()}`,
          role: "user",
          text: trimmedQuery,
          citations: [],
          detected_language: language,
        },
      ]);

      const response = await sendChat({
        sessionId: session.session_id,
        token: session.token,
        query: trimmedQuery,
        language,
      });

      await new Promise((resolve) => {
        setTimeout(resolve, 800);
      });

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          text: response.answer,
          citations: response.citations || [],
          detected_language: response.detected_language,
          created_at: response.created_at,
        },
      ]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSending(false);
    }
  }

  if (loading) {
    return (
      <main className="bg-light min-vh-100 d-flex align-items-center justify-content-center">
        <div className="text-success fw-semibold">Loading GovSaathi...</div>
      </main>
    );
  }

  function startNewChat() {
    localStorage.removeItem(SESSION_STORAGE_KEY);
    window.location.reload();
  }

  function clearError() {
    setError("");
  }

  function retryInitialization() {
    window.location.reload();
  }

  return (
    <main className="bg-light min-vh-100 py-4">
      <Container>
        <Card className="shadow-sm border-0">
          <Card.Header className="bg-success text-white p-4">
            <div className="d-flex justify-content-between align-items-start gap-3">
              <div>
                <h1 className="h3 mb-2">GovSaathi</h1>
                <p className="mb-0">
                  Ask questions about government schemes and services.
                </p>
              </div>

              <button
                type="button"
                className="btn btn-outline-light btn-sm"
                onClick={startNewChat}
              >
                New chat
              </button>
            </div>
          </Card.Header>

          <Card.Body className="p-4">
            {error && (
              <Alert variant="danger" dismissible onClose={clearError}>
                <Alert.Heading>Something went wrong</Alert.Heading>

                <p className="mb-3">{error}</p>

                <Button
                  variant="outline-danger"
                  size="sm"
                  onClick={retryInitialization}
                >
                  Try again
                </Button>
              </Alert>
            )}

            <div className="mb-4">
              {messages.length === 0 && !error && (
                <div className="text-center text-secondary py-5">
                  No messages yet. Ask your first question.
                </div>
              )}

              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}

              {sending && (
                <div className="d-flex justify-content-start mb-3">
                  <div className="bg-light border rounded p-3 text-secondary">
                    GovSaathi is thinking...
                  </div>
                </div>
              )}
            </div>

            <ChatInput
              onSend={handleSend}
              loading={sending}
              language={language}
              onLanguageChange={setLanguage}
            />
          </Card.Body>
        </Card>
      </Container>
    </main>
  );
}

export default App;

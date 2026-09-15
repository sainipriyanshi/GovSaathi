import { useState } from "react";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import InputGroup from "react-bootstrap/InputGroup";

function ChatInput({ onSend, loading, language, onLanguageChange }) {
  const [query, setQuery] = useState("");
  const [validated, setValidated] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const trimmedQuery = query.trim();

    if (!trimmedQuery || loading) {
      setValidated(true);
      return;
    }

    if (!form.checkValidity()) {
      event.stopPropagation();
      setValidated(true);
      return;
    }

    try {
      await onSend(trimmedQuery);
      setQuery("");
      setValidated(false);
    } catch {
      setValidated(true);
    }
  }

  function handleQueryChange(event) {
    setQuery(event.target.value);

    if (event.target.value.trim()) {
      setValidated(false);
    }
  }

  return (
    <Form
      noValidate
      validated={validated}
      onSubmit={handleSubmit}
    >
      <div className="d-flex gap-2 align-items-start">
        <Form.Select
          value={language}
          onChange={(event) => onLanguageChange(event.target.value)}
          disabled={loading}
          style={{ maxWidth: "130px" }}
          aria-label="Select language"
        >
          <option value="en">English</option>
          <option value="hi">Hindi</option>
        </Form.Select>

        <div className="flex-grow-1">
          <Form.Control
            required
            type="text"
            placeholder="Ask GovSaathi a question..."
            value={query}
            onChange={handleQueryChange}
            disabled={loading}
            aria-label="Your question"
            isInvalid={validated && !query.trim()}
          />

          {validated && !query.trim() && (
            <div className="invalid-feedback d-block">
              Please enter a question.
            </div>
          )}
        </div>

        <Button variant="success" type="submit" disabled={loading}>
          {loading ? "Sending..." : "Send"}
        </Button>
      </div>
    </Form>
  );
}

export default ChatInput;

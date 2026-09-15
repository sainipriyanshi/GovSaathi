import CitationPanel from "./CitationPanel";

function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`d-flex mb-3 ${
        isUser ? "justify-content-end" : "justify-content-start"
      }`}
    >
      <div
        className={`rounded p-3 ${
          isUser ? "bg-primary text-white" : "bg-light border"
        }`}
        style={{ maxWidth: "75%" }}
      >
        <div
          className={`small fw-bold mb-1 ${
            isUser ? "text-white" : "text-success"
          }`}
        >
          {isUser ? "You" : "GovSaathi"}
        </div>

        <div>{message.text}</div>

        {!isUser && (
          <CitationPanel citations={message.citations} />
        )}
      </div>
    </div>
  );
}

export default MessageBubble;
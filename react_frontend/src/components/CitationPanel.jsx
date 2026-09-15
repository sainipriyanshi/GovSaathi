import ListGroup from "react-bootstrap/ListGroup";

function CitationPanel({ citations }) {
  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="border-top mt-3 pt-3">
      <div className="small fw-bold text-secondary mb-2">
        Sources
      </div>

      <ListGroup>
        {citations.map((citation, index) => (
          <ListGroup.Item
            key={`${citation.title}-${index}`}
            className="px-3 py-2"
          >
            <div className="fw-semibold">
              {citation.title}
            </div>

            <div className="small text-muted">
              Source: {citation.source}
            </div>

            {citation.page !== null &&
              citation.page !== undefined && (
                <div className="small text-muted">
                  Page: {citation.page}
                </div>
              )}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </div>
  );
}

export default CitationPanel;
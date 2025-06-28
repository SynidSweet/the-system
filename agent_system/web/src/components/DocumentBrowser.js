import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './DocumentBrowser.css';

function DocumentBrowser({ apiBaseUrl }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('');
  const [showMarkdownPreview, setShowMarkdownPreview] = useState(true);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/documents`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      const documents = Array.isArray(data.documents) ? data.documents : [];
      setDocuments(documents);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Failed to load documents');
      setDocuments([]);
      setLoading(false);
    }
  };

  const selectDocument = async (doc) => {
    try {
      const response = await fetch(`${apiBaseUrl}/documents/${doc.name}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setSelectedDoc(data);
      setEditedContent(data.content || '');
      setEditMode(false);
      setError(null);
    } catch (err) {
      console.error('Error fetching document details:', err);
      setError('Failed to load document details');
    }
  };

  const handleEdit = () => {
    setEditMode(true);
  };

  const handleCancel = () => {
    setEditMode(false);
    setEditedContent(selectedDoc.content);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${apiBaseUrl}/documents/${selectedDoc.name}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: editedContent,
          updated_by: 0 // System update
        }),
      });

      if (response.ok) {
        setSelectedDoc(prev => ({
          ...prev,
          content: editedContent,
          updated_at: new Date().toISOString()
        }));
        setEditMode(false);
        fetchDocuments(); // Refresh the list
      } else {
        throw new Error('Failed to save');
      }
    } catch (err) {
      setError('Failed to save document');
    } finally {
      setSaving(false);
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const filteredDocs = documents.filter(doc => 
    (doc.name || '').toLowerCase().includes(filter.toLowerCase()) ||
    (doc.title || '').toLowerCase().includes(filter.toLowerCase()) ||
    (doc.category || '').toLowerCase().includes(filter.toLowerCase())
  );

  // Group documents by category
  const docsByCategory = filteredDocs.reduce((acc, doc) => {
    if (!acc[doc.category]) {
      acc[doc.category] = [];
    }
    acc[doc.category].push(doc);
    return acc;
  }, {});

  if (loading) {
    return <div className="document-browser loading">Loading documents...</div>;
  }

  return (
    <div className="document-browser">
      <div className="document-list">
        <h2>Documents</h2>
        <input
          type="text"
          placeholder="Filter documents..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="filter-input"
        />
        
        <div className="document-categories">
          {Object.entries(docsByCategory).map(([category, docs]) => (
            <div key={category} className="doc-category">
              <h3 className="category-name">{category}</h3>
              <div className="doc-items">
                {docs.map(doc => (
                  <div
                    key={doc.name}
                    className={`doc-item ${selectedDoc?.name === doc.name ? 'selected' : ''}`}
                    onClick={() => selectDocument(doc)}
                  >
                    <div className="doc-name">{doc.name}</div>
                    <div className="doc-meta">
                      <span className="doc-format">{doc.format || 'text'}</span>
                      <span className="doc-size">{formatSize(doc.size || 0)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="document-details">
        {selectedDoc ? (
          <>
            <div className="doc-header">
              <div>
                <h2>{selectedDoc.title || selectedDoc.name}</h2>
                <div className="doc-info">
                  <span className="doc-category-badge">{selectedDoc.category || 'general'}</span>
                  <span className="doc-format-badge">{selectedDoc.format || 'text'}</span>
                </div>
              </div>
              <div className="doc-actions">
                {!editMode && selectedDoc.format === 'markdown' && (
                  <button
                    onClick={() => setShowMarkdownPreview(!showMarkdownPreview)}
                    className="toggle-button"
                  >
                    {showMarkdownPreview ? 'Show Raw' : 'Show Preview'}
                  </button>
                )}
                {!editMode ? (
                  <button onClick={handleEdit} className="edit-button">Edit</button>
                ) : (
                  <>
                    <button 
                      onClick={handleSave} 
                      className="save-button"
                      disabled={saving}
                    >
                      {saving ? 'Saving...' : 'Save'}
                    </button>
                    <button 
                      onClick={handleCancel} 
                      className="cancel-button"
                      disabled={saving}
                    >
                      Cancel
                    </button>
                  </>
                )}
              </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="doc-content-section">
              <div className="field-group">
                <label>
                  Content 
                  {!editMode && selectedDoc.format === 'markdown' && (
                    <span className="preview-label"> (Markdown Preview)</span>
                  )}
                </label>
                {editMode ? (
                  <textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    className="content-editor"
                    rows={25}
                    spellCheck={false}
                  />
                ) : (
                  selectedDoc.format === 'markdown' && showMarkdownPreview ? (
                    <div className="markdown-preview">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code({node, inline, className, children, ...props}) {
                            const match = /language-(\w+)/.exec(className || '')
                            return !inline && match ? (
                              <pre className="code-block">
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              </pre>
                            ) : (
                              <code className="inline-code" {...props}>
                                {children}
                              </code>
                            )
                          },
                          table({node, ...props}) {
                            return (
                              <div className="table-wrapper">
                                <table {...props} />
                              </div>
                            )
                          }
                        }}
                      >
                        {selectedDoc.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <pre className="content-display">{selectedDoc.content}</pre>
                  )
                )}
              </div>

              {!editMode && (
                <div className="doc-metadata">
                  <div className="metadata-item">
                    <span className="meta-label">Name:</span>
                    <span className="meta-value">{selectedDoc.name}</span>
                  </div>
                  <div className="metadata-item">
                    <span className="meta-label">Format:</span>
                    <span className="meta-value">{selectedDoc.format}</span>
                  </div>
                  <div className="metadata-item">
                    <span className="meta-label">Version:</span>
                    <span className="meta-value">{selectedDoc.version || '1.0'}</span>
                  </div>
                  <div className="metadata-item">
                    <span className="meta-label">Access Level:</span>
                    <span className="meta-value">{selectedDoc.access_level || 'system'}</span>
                  </div>
                  <div className="metadata-item">
                    <span className="meta-label">Created:</span>
                    <span className="meta-value">
                      {selectedDoc.created_at ? new Date(selectedDoc.created_at).toLocaleString() : 'N/A'}
                    </span>
                  </div>
                  <div className="metadata-item">
                    <span className="meta-label">Updated:</span>
                    <span className="meta-value">
                      {selectedDoc.updated_at ? new Date(selectedDoc.updated_at).toLocaleString() : 'N/A'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="no-selection">Select a document to view details</div>
        )}
      </div>
    </div>
  );
}

export default DocumentBrowser;
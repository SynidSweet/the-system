import React, { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './DocumentBrowser.css';
import { Document, DocumentBrowserProps } from '../types';

function DocumentBrowser({ apiBaseUrl }: DocumentBrowserProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [editMode, setEditMode] = useState<boolean>(false);
  const [editedContent, setEditedContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('');
  const [showMarkdownPreview, setShowMarkdownPreview] = useState<boolean>(true);

  const fetchDocuments = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/documents`);
      const data = await response.json();
      setDocuments(data.documents);
      setLoading(false);
    } catch (err) {
      setError('Failed to load documents');
      setLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const selectDocument = useCallback(async (doc: Document) => {
    try {
      const response = await fetch(`${apiBaseUrl}/documents/${doc.name}`);
      const data = await response.json();
      setSelectedDoc(data);
      setEditedContent(data.content);
      setEditMode(false);
    } catch (err) {
      setError('Failed to load document details');
    }
  }, [apiBaseUrl]);

  const handleEdit = useCallback(() => {
    setEditMode(true);
  }, []);

  const handleCancel = useCallback(() => {
    setEditMode(false);
    if (selectedDoc) {
      setEditedContent(selectedDoc.content);
    }
  }, [selectedDoc]);

  const handleSave = useCallback(async () => {
    if (!selectedDoc) return;
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
        setSelectedDoc(prev => prev ? ({
          ...prev,
          content: editedContent,
          updated_at: new Date().toISOString()
        }) : null);
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
  }, [apiBaseUrl, selectedDoc, editedContent, fetchDocuments]);

  const formatSize = useCallback((bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }, []);

  const filteredDocs = documents.filter(doc => 
    doc.name.toLowerCase().includes(filter.toLowerCase()) ||
    doc.title.toLowerCase().includes(filter.toLowerCase()) ||
    doc.category.toLowerCase().includes(filter.toLowerCase())
  );

  // Group documents by category
  const docsByCategory = filteredDocs.reduce((acc: Record<string, Document[]>, doc) => {
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
                      <span className="doc-format">{doc.format}</span>
                      <span className="doc-size">{formatSize(doc.size)}</span>
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
                  <span className="doc-category-badge">{selectedDoc.category}</span>
                  <span className="doc-format-badge">{selectedDoc.format}</span>
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
                          code(props: any) {
                            const {node, inline, className, children, ...rest} = props;
                            const match = /language-(\w+)/.exec(className || '')
                            return !inline && match ? (
                              <pre className="code-block">
                                <code className={className} {...rest}>
                                  {children}
                                </code>
                              </pre>
                            ) : (
                              <code className="inline-code" {...rest}>
                                {children}
                              </code>
                            )
                          },
                          table(props: any) {
                            const {node, ...rest} = props;
                            return (
                              <div className="table-wrapper">
                                <table {...rest} />
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
                      {new Date(selectedDoc.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="metadata-item">
                    <span className="meta-label">Updated:</span>
                    <span className="meta-value">
                      {new Date(selectedDoc.updated_at).toLocaleString()}
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
import React, { useState, useEffect } from 'react'

interface Field {
  name: string
  type: string
  nested_fields?: Field[]
  sub_fields?: Field[]
}

interface IndexInfo {
  name: string
  doc_count: string
  size: string
  configured: boolean
  fields: Field[]
  field_count: number
  error?: string
}

interface DatabasePopupProps {
  isOpen: boolean
  onClose: () => void
  esInfo: any
}

const DatabasePopup: React.FC<DatabasePopupProps> = ({ isOpen, onClose, esInfo }) => {
  const [indicesWithFields, setIndicesWithFields] = useState<IndexInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedIndices, setExpandedIndices] = useState<Set<string>>(new Set())
  const [expandedFields, setExpandedFields] = useState<Set<string>>(new Set())

  const fetchIndicesWithFields = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/es/indices-fields')
      const data = await response.json()
      
      if (data.enabled === false) {
        setError('Elasticsearch غیرفعال است')
        setIndicesWithFields([])
        return
      }
      
      if (data.error) {
        setError(data.error)
        setIndicesWithFields([])
        return
      }
      
      setIndicesWithFields(data.indices || [])
    } catch (err) {
      setError('خطا در دریافت اطلاعات پایگاه داده')
      setIndicesWithFields([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen && esInfo?.enabled) {
      fetchIndicesWithFields()
    }
  }, [isOpen, esInfo])

  const toggleIndex = (indexName: string) => {
    const newExpanded = new Set(expandedIndices)
    if (newExpanded.has(indexName)) {
      newExpanded.delete(indexName)
    } else {
      newExpanded.add(indexName)
    }
    setExpandedIndices(newExpanded)
  }

  const toggleField = (fieldKey: string) => {
    const newExpanded = new Set(expandedFields)
    if (newExpanded.has(fieldKey)) {
      newExpanded.delete(fieldKey)
    } else {
      newExpanded.add(fieldKey)
    }
    setExpandedFields(newExpanded)
  }

  const renderField = (field: Field, parentPath: string = '', level: number = 0) => {
    const fieldKey = `${parentPath}.${field.name}`
    const isExpanded = expandedFields.has(fieldKey)
    const hasChildren = (field.nested_fields && field.nested_fields.length > 0) || 
                       (field.sub_fields && field.sub_fields.length > 0)
    
    const indent = level * 20

    return (
      <div key={fieldKey} className="field-item">
        <div 
          className="field-header"
          style={{ paddingRight: `${indent}px` }}
          onClick={() => hasChildren && toggleField(fieldKey)}
        >
          <div className="field-info">
            <div className="field-main">
              <span className="field-name">{field.name}</span>
              <span className="field-type">{field.type}</span>
            </div>
            {hasChildren && (
              <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>
                {isExpanded ? '▼' : '▶'}
              </span>
            )}
          </div>
        </div>
        
        {isExpanded && hasChildren && (
          <div className="field-children">
            {field.nested_fields?.map(nestedField => 
              renderField(nestedField, fieldKey, level + 1)
            )}
            {field.sub_fields?.map(subField => 
              renderField(subField, fieldKey, level + 1)
            )}
          </div>
        )}
      </div>
    )
  }

  const renderIndex = (index: IndexInfo) => {
    const isExpanded = expandedIndices.has(index.name)
    const hasFields = index.fields && index.fields.length > 0

    return (
      <div key={index.name} className="index-item">
        <div 
          className="index-header"
          onClick={() => toggleIndex(index.name)}
        >
          <div className="index-info">
            <div className="index-details">
              <span className="index-name">{index.name}</span>
              <div className="index-meta">
                <span className="doc-count">{index.doc_count} سند</span>
                <span className="index-size">{index.size}</span>
                <span className="field-count">{index.field_count} فیلد</span>
                {index.configured && <span className="configured-badge">پیکربندی شده</span>}
              </div>
            </div>
            <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>
              {hasFields ? (isExpanded ? '▼' : '▶') : '○'}
            </span>
          </div>
        </div>
        
        {isExpanded && (
          <div className="index-fields">
            {index.error ? (
              <div className="error-message">خطا: {index.error}</div>
            ) : hasFields ? (
              <div className="fields-list">
                {index.fields.map(field => renderField(field, index.name))}
              </div>
            ) : (
              <div className="no-fields">هیچ فیلدی یافت نشد</div>
            )}
          </div>
        )}
      </div>
    )
  }

  if (!isOpen) return null

  return (
    <div className="database-popup-overlay" onClick={onClose}>
      <div className="database-popup" onClick={(e) => e.stopPropagation()}>
        <div className="database-header">
          <h3>🗄️ ساختار پایگاه داده</h3>
          <button className="database-confirm" onClick={onClose}>
            ✓ تایید
          </button>
        </div>
        
        <div className="database-content">
          {!esInfo?.enabled ? (
            <div className="database-section">
              <div className="status-inactive">
                <p>اتصال به پایگاه داده غیرفعال است</p>
              </div>
            </div>
          ) : loading ? (
            <div className="database-section">
              <div className="loading">
                <div className="loading-spinner"></div>
                <p>در حال دریافت اطلاعات...</p>
              </div>
            </div>
          ) : error ? (
            <div className="database-section">
              <div className="error">
                <p>خطا: {error}</p>
                <button onClick={fetchIndicesWithFields}>تلاش مجدد</button>
              </div>
            </div>
          ) : (
            <div className="database-section">
              <div className="tree-header">
                <h4>ایندکس‌ها ({indicesWithFields.length})</h4>
                <button className="refresh-button" onClick={fetchIndicesWithFields}>
                  🔄 بروزرسانی
                </button>
              </div>
              
              {indicesWithFields.length === 0 ? (
                <div className="no-indices">هیچ ایندکسی یافت نشد</div>
              ) : (
                <div className="indices-list">
                  {indicesWithFields.map(renderIndex)}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      <style>{`
        .database-popup-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(8px);
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
          animation: fadeIn 0.3s ease-out;
        }
        
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        
        .database-popup {
          background: white;
          border-radius: 16px;
          box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.15),
            0 8px 16px rgba(0, 0, 0, 0.1);
          max-width: 800px;
          width: 90%;
          max-height: 80vh;
          overflow-y: auto;
          animation: slideInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .database-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem;
          border-bottom: 1px solid #e5e7eb;
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          border-radius: 16px 16px 0 0;
        }
        
        .database-header h3 {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 600;
          color: #1f2937;
        }
        
        .database-confirm {
          background: none;
          color: #22c55e;
          border: 2px solid #22c55e;
          border-radius: 8px;
          padding: 0.5rem 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 0.9rem;
        }
        
        .database-confirm:hover {
          background: #22c55e;
          color: white;
          transform: translateY(-1px);
          box-shadow: 0 2px 4px rgba(34, 197, 94, 0.3);
        }
        
        .database-content {
          padding: 1.5rem;
        }
        
        .database-section {
          margin-bottom: 1.5rem;
        }
        
        .database-section:last-child {
          margin-bottom: 0;
        }
        
        .status-inactive {
          text-align: center;
          padding: 40px;
          color: #6b7280;
        }
        
        .loading {
          text-align: center;
          padding: 40px;
        }
        
        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #e5e7eb;
          border-top: 4px solid #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 16px;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        .error {
          text-align: center;
          padding: 40px;
          color: #ef4444;
        }
        
        .error button {
          margin-top: 16px;
          padding: 8px 16px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
        }
        
        .tree-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }
        
        .tree-header h4 {
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
          color: #374151;
        }
        
        .refresh-button {
          padding: 6px 12px;
          background: #f3f4f6;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.875rem;
          color: #374151;
          font-weight: 500;
        }
        
        .refresh-button:hover {
          background: #e5e7eb;
          color: #1f2937;
        }
        
        /* Dark mode refresh button */
        .dark-mode .refresh-button {
          background: #374151;
          border: 1px solid #4b5563;
          color: #f3f4f6;
        }
        
        .dark-mode .refresh-button:hover {
          background: #4b5563;
          color: #ffffff;
        }
        
        .no-indices {
          text-align: center;
          padding: 40px;
          color: #6b7280;
        }
        
        .indices-list {
          space-y: 8px;
        }
        
        .index-item {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          margin-bottom: 8px;
        }
        
        .index-header {
          padding: 12px 16px;
          cursor: pointer;
          background: #f9fafb;
          border-radius: 8px 8px 0 0;
        }
        
        .index-header:hover {
          background: #f3f4f6;
        }
        
        .index-info {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        
        .expand-icon {
          color: #6b7280;
          font-size: 0.875rem;
          width: 16px;
          text-align: center;
          flex-shrink: 0;
          transition: transform 0.2s ease;
          transform: rotate(180deg);
        }
        
        .expand-icon.expanded {
          transform: rotate(90deg);
        }
        
        .index-details {
          flex: 1;
        }
        
        .index-name {
          font-weight: 600;
          color: #1f2937;
          display: block;
          margin-bottom: 4px;
        }
        
        .index-meta {
          display: flex;
          gap: 16px;
          font-size: 0.875rem;
          color: #6b7280;
        }
        
        .configured-badge {
          background: #10b981;
          color: white;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 0.75rem;
        }
        
        .index-fields {
          padding: 16px;
          background: white;
          border-top: 1px solid #e5e7eb;
        }
        
        .error-message {
          color: #ef4444;
          font-style: italic;
        }
        
        .no-fields {
          color: #6b7280;
          font-style: italic;
        }
        
        .fields-list {
          space-y: 4px;
        }
        
        .field-item {
          border-left: 2px solid #e5e7eb;
          margin-left: 8px;
        }
        
        .field-header {
          padding: 6px 12px;
          cursor: pointer;
          border-radius: 4px;
        }
        
        .field-header:hover {
          background: #f9fafb;
        }
        
        .field-info {
          display: flex;
          align-items: center;
          gap: 8px;
          justify-content: space-between;
        }
        
        .field-main {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;
        }
        
        .field-name {
          font-weight: 500;
          color: #1f2937;
        }
        
        .field-type {
          background: #e0e7ff;
          color: #3730a3;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
        }
        
        .field-children {
          margin-right: 16px;
          border-left: 1px solid #d1d5db;
        }
        
        /* Dark mode styles */
        .dark-mode .database-popup {
          background: #1e293b;
          border: 1px solid #334155;
        }
        
        .dark-mode .database-header {
          background: linear-gradient(135deg, #334155 0%, #475569 100%);
          border-bottom: 1px solid #475569;
        }
        
        .dark-mode .database-header h3 {
          color: #f1f5f9;
        }
        
        .dark-mode .database-confirm {
          color: #34d399;
          border-color: #34d399;
        }
        
        .dark-mode .database-confirm:hover {
          background: #34d399;
          color: #1f2937;
          box-shadow: 0 2px 4px rgba(52, 211, 153, 0.3);
        }
        
        .dark-mode .tree-header h4 {
          color: #e2e8f0;
        }
        
        .dark-mode .refresh-button {
          background: #374151;
          border: 1px solid #4b5563;
          color: #f3f4f6;
        }
        
        .dark-mode .refresh-button:hover {
          background: #4b5563;
          color: #ffffff;
        }
        
        .dark-mode .status-inactive {
          color: #9ca3af;
        }
        
        .dark-mode .loading {
          color: #e2e8f0;
        }
        
        .dark-mode .error {
          color: #fca5a5;
        }
        
        .dark-mode .no-indices {
          color: #9ca3af;
        }
        
        .dark-mode .index-item {
          border: 1px solid #374151;
          background: #1e293b;
        }
        
        .dark-mode .index-header {
          background: #334155;
        }
        
        .dark-mode .index-header:hover {
          background: #3f4a5c;
        }
        
        .dark-mode .index-name {
          color: #f1f5f9;
        }
        
        .dark-mode .index-meta {
          color: #9ca3af;
        }
        
        .dark-mode .configured-badge {
          background: #10b981;
          color: white;
        }
        
        .dark-mode .index-fields {
          background: #1e293b;
          border-top: 1px solid #374151;
        }
        
        .dark-mode .field-header:hover {
          background: #334155;
        }
        
        .dark-mode .field-main {
          color: #f1f5f9;
        }
        
        .dark-mode .field-name {
          color: #f1f5f9;
        }
        
        .dark-mode .field-type {
          background: #1e3a8a;
          color: #93c5fd;
        }
        
        .dark-mode .field-item {
          border-left: 2px solid #374151;
        }
        
        .dark-mode .field-children {
          border-left: 1px solid #4b5563;
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
          .database-popup {
            width: 95%;
            max-height: 90vh;
          }
          
          .database-header {
            padding: 1rem;
          }
          
          .database-content {
            padding: 1rem;
          }
        }
      `}</style>
    </div>
  )
}

export default DatabasePopup

import React, { useState } from 'react';
import { X } from 'lucide-react';
import { FileDropZone } from './FileDropZone.tsx';

interface BookUploaderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File, title?: string, author?: string) => Promise<any>;
}

export const BookUploaderModal: React.FC<BookUploaderModalProps> = ({
  isOpen,
  onClose,
  onUpload,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      await onUpload(file, title.trim() || undefined, author.trim() || undefined);
      setFile(null);
      setTitle('');
      setAuthor('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Upload Audiobook Document</h3>
          <button onClick={onClose} className="modal-close"><X size={20} /></button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <FileDropZone selectedFile={file} onFileSelected={setFile} />

          <div className="form-group">
            <label>Title (Optional):</label>
            <input
              type="text"
              placeholder="Leave empty to use filename"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Author (Optional):</label>
            <input
              type="text"
              placeholder="e.g. Orville Wright"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
            />
          </div>

          {error && <div className="form-error">{error}</div>}

          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-secondary" disabled={isUploading}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={!file || isUploading}>
              {isUploading ? 'Parsing & Ingesting...' : 'Upload & Catalog'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

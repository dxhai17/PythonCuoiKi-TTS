import React, { useRef, useState } from 'react';
import { UploadCloud } from 'lucide-react';

interface FileDropZoneProps {
  onFileSelected: (file: File) => void;
  selectedFile: File | null;
}

export const FileDropZone: React.FC<FileDropZoneProps> = ({ onFileSelected, selectedFile }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      validateAndSelect(file);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSelect(e.target.files[0]);
    }
  };

  const validateAndSelect = (file: File) => {
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (ext !== '.txt' && ext !== '.md') {
      alert('Only .txt and .md files are supported');
      return;
    }
    onFileSelected(file);
  };

  return (
    <div
      className={`dropzone ${isDragOver ? 'drag-over' : ''} ${selectedFile ? 'has-file' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleInputChange}
        accept=".txt,.md"
        style={{ display: 'none' }}
      />
      <UploadCloud size={36} className="dropzone-icon" />
      {selectedFile ? (
        <div className="file-info">
          <p className="file-name">{selectedFile.name}</p>
          <p className="file-size">{(selectedFile.size / 1024).toFixed(1)} KB</p>
        </div>
      ) : (
        <div className="dropzone-text">
          <p className="prompt-primary">Drag & drop your .txt or .md book here</p>
          <p className="prompt-secondary">or click to browse from your device</p>
        </div>
      )}
    </div>
  );
};

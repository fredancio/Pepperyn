'use client';
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { clsx } from 'clsx';

interface FileUploadZoneProps {
  onFileSelect: (file: File) => void;
  accept?: Record<string, string[]>;
  maxSize?: number;
  disabled?: boolean;
}

const DEFAULT_ACCEPT = {
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls'],
  'text/csv': ['.csv'],
  'application/pdf': ['.pdf'],
};

export function FileUploadZone({
  onFileSelect,
  accept = DEFAULT_ACCEPT,
  maxSize = 25 * 1024 * 1024, // 25MB
  disabled = false,
}: FileUploadZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, isDragReject, fileRejections } = useDropzone({
    onDrop,
    accept,
    maxSize,
    maxFiles: 1,
    disabled,
  });

  const hasError = fileRejections.length > 0;

  return (
    <div
      {...getRootProps()}
      className={clsx(
        'border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200',
        isDragActive && !isDragReject && 'border-[#1B73E8] bg-blue-50',
        isDragReject && 'border-red-400 bg-red-50',
        hasError && 'border-red-400',
        !isDragActive && !hasError && 'border-gray-200 hover:border-[#1B73E8] hover:bg-blue-50/30',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      <input {...getInputProps()} />

      <div className="flex flex-col items-center gap-3">
        {isDragActive ? (
          <div className="w-14 h-14 bg-[#1B73E8] rounded-2xl flex items-center justify-center animate-bounce">
            <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
        ) : (
          <div className="w-14 h-14 bg-[#EFF6FF] rounded-2xl flex items-center justify-center">
            <svg className="w-7 h-7 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        )}

        <div>
          {isDragActive ? (
            <p className="text-[#1B73E8] font-semibold text-sm">
              {isDragReject ? 'Format non supporté' : 'Déposez le fichier ici'}
            </p>
          ) : (
            <>
              <p className="text-[#1A1A2E] font-semibold text-sm mb-1">
                Glissez-déposez votre fichier ici
              </p>
              <p className="text-[#5F6368] text-xs">
                ou <span className="text-[#1B73E8] font-medium">cliquez pour choisir</span>
              </p>
            </>
          )}
        </div>

        <div className="flex gap-2 flex-wrap justify-center">
          {['Excel', 'CSV', 'PDF'].map(fmt => (
            <span key={fmt} className="px-2 py-0.5 bg-gray-100 text-[#5F6368] text-xs rounded-full font-medium">
              {fmt}
            </span>
          ))}
          <span className="px-2 py-0.5 bg-gray-100 text-[#5F6368] text-xs rounded-full font-medium">
            Max 25Mo
          </span>
        </div>
      </div>

      {hasError && fileRejections[0] && (
        <p className="mt-3 text-xs text-red-500">
          {fileRejections[0].errors[0]?.code === 'file-too-large'
            ? 'Fichier trop volumineux (max 25Mo)'
            : 'Format de fichier non supporté'}
        </p>
      )}
    </div>
  );
}

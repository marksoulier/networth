import { forwardRef, type ReactNode } from 'react';

interface ModalContainerProps {
  children: ReactNode;
  className?: string;
}

const ModalContainer = forwardRef<HTMLDivElement, ModalContainerProps>(
  ({ children, className = '' }, ref) => {
    return (
      <div ref={ref} className={`fixed inset-0 flex items-center justify-center z-50 ${className}`}>
        <div className="relative bg-white rounded-lg border border-gray-200 shadow-lg p-6 w-[500px] max-w-[90vw]">
          {children}
        </div>
      </div>
    );
  }
);

ModalContainer.displayName = 'ModalContainer';

export default ModalContainer; 
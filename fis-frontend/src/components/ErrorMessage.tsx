import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';

interface ErrorMessageProps {
  title?: string;
  message?: string;
  showHomeButton?: boolean;
}

export default function ErrorMessage({
  title = 'Something went wrong',
  message = 'We encountered an error while loading this page. Please try again.',
  showHomeButton = true,
}: ErrorMessageProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <ExclamationTriangleIcon className="h-16 w-16 text-red-500 mb-4" />
      <h2 className="text-2xl font-bold text-gray-900 mb-2">{title}</h2>
      <p className="text-gray-600 text-center max-w-md mb-6">{message}</p>
      {showHomeButton && (
        <Link to="/" className="btn-primary">
          ← Back to Home
        </Link>
      )}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  message,
}: {
  icon?: React.ReactNode;
  title: string;
  message: string;
}) {
  return (
    <div className="text-center py-12">
      {icon && <div className="flex justify-center mb-4">{icon}</div>}
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{message}</p>
    </div>
  );
}

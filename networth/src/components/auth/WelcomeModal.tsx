import * as Dialog from '@radix-ui/react-dialog';

interface WelcomeModalProps {
  onBegin: () => void;
}

const WelcomeModal = ({ onBegin }: WelcomeModalProps) => {
  return (
    <Dialog.Portal>
      <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        <div className="text-center space-y-6">
          <Dialog.Title className="text-3xl font-bold text-gray-900">
            Welcome to NetWorth
          </Dialog.Title>
          
          <p className="text-gray-600 text-lg">
            Your journey to financial visualization begins here. Explore your data with our interactive tools.
          </p>

          <div className="pt-4">
            <button
              type="button"
              onClick={onBegin}
              className="inline-flex items-center justify-center px-6 py-3 text-lg font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              Begin
            </button>
          </div>
        </div>
    </Dialog.Portal>
  );
};

export default WelcomeModal; 


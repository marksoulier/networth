import { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { supabase, type User } from './lib/supabase';
import AuthModal from './components/auth/AuthModal';
import WelcomeModal from './components/auth/WelcomeModal';
import { Visualization } from './components/visualization/Visualization';
import TimelineAnnotation from './components/UI/TimelineAnnotation';

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(true);
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session on mount
    const checkSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.user) {
          setUser(session.user);
          setShowAuthModal(false);
        }
      } catch (error) {
        console.error('Error checking session:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkSession();

    // Subscribe to auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      if (session?.user) {
        setShowAuthModal(false);
        setShowWelcomeModal(true);
      } else {
        setShowAuthModal(true);
        setShowWelcomeModal(false);
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Main content with blur effect when modals are open */}
      <div className={`relative w-full h-screen ${(showAuthModal || showWelcomeModal) ? 'blur-sm pointer-events-none' : ''}`}>
        {/* <TimelineAnnotation /> */}

        <Visualization />
      </div>

      {/* Auth Modal - Cannot be closed by clicking outside */}
      <Dialog.Root open={showAuthModal} onOpenChange={(open) => {
        // Only allow closing if user is authenticated
        if (user) {
          setShowAuthModal(open);
        }
      }}>
        <AuthModal />
      </Dialog.Root>

      {/* Welcome Modal */}
      <Dialog.Root open={showWelcomeModal} onOpenChange={setShowWelcomeModal}>
        <WelcomeModal onBegin={() => setShowWelcomeModal(false)} />
      </Dialog.Root>
    </div>
  );
}

export default App;

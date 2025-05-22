import { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { supabase, type User } from './lib/supabase';
import AuthModal from './components/auth/AuthModal';
import WelcomeModal from './components/auth/WelcomeModal';
import { Visualization } from './components/visualization/Visualization';
import { OverlayControls } from './components/UI/OverlayControls';

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session on mount
    const checkSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.user) {
          setUser(session.user);
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
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-slate-900">
      {/* Main visualization */}
      <div className="absolute inset-0">
        <Visualization />
      </div>

      {/* Overlay controls */}
      <OverlayControls
        onSignOut={handleSignOut}
        onShowWelcome={() => setShowWelcomeModal(true)}
      />

      {/* Auth Modal */}
      <Dialog.Root open={showAuthModal} onOpenChange={setShowAuthModal}>
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

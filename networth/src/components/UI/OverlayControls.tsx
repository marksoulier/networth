import { Button } from "./button";

interface OverlayControlsProps {
  onSignOut: () => void;
  onShowWelcome: () => void;
}

export function OverlayControls({ onSignOut, onShowWelcome }: OverlayControlsProps) {
  return (
    <>
      <Button
        variant="outline"
        onClick={onShowWelcome}
        className="absolute top-4 right-4 z-50 bg-white/10 hover:bg-white/20 text-white border-white/20 z-50"
      >
        Welcome
      </Button>
      <Button
        variant="outline"
        onClick={onSignOut}
        className="absolute top-4 right-32 z-50 bg-white/10 hover:bg-white/20 text-white border-white/20 z-50"
      >
        Sign Out
      </Button>
    </>
  );
} 
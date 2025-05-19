import { Info } from "lucide-react";

export default function TimelineAnnotation() {
  return (
    <div className="relative flex flex-col items-center">
      {/* Main box */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-lg px-4 py-3 flex items-center justify-center relative z-10 border-2 border-blue-500">
        <Info className="w-5 h-5 text-blue-500" />
      </div>

      {/* Drop at bottom center */}
      <div className="w-3 h-3 bg-white dark:bg-gray-900 rotate-45 shadow-md absolute bottom-0 translate-y-1/2 z-0 border-r border-b border-blue-500" />
    </div>
  );
}

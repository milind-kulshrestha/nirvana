import useLayoutStore from '../../stores/layoutStore';
import RunSteps from '../rightrail/RunSteps';
import SourcesPanel from '../rightrail/SourcesPanel';
import SkillsPalette from '../rightrail/SkillsPalette';
import { X, ListOrdered, Database, Sparkles } from 'lucide-react';

const TABS = [
  { key: 'steps', label: 'Steps', icon: ListOrdered },
  { key: 'sources', label: 'Sources', icon: Database },
  { key: 'skills', label: 'Skills', icon: Sparkles },
];

const TAB_CONTENT = {
  steps: RunSteps,
  sources: SourcesPanel,
  skills: SkillsPalette,
};

export default function RightRail() {
  const { rightRailOpen, rightRailTab, setRightRailTab, closeRightRail } = useLayoutStore();

  if (!rightRailOpen) return null;

  const Content = TAB_CONTENT[rightRailTab] || RunSteps;

  return (
    <aside className="w-80 h-full flex flex-col bg-card border-l border-border shrink-0 transition-all duration-normal">
      {/* Header */}
      <div className="flex items-center justify-between h-12 px-3 border-b border-border shrink-0">
        <div className="flex gap-0.5 bg-muted/60 rounded-lg p-0.5">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const active = rightRailTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setRightRailTab(tab.key)}
                className={`flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium transition-all duration-fast ${
                  active
                    ? 'bg-background shadow-sm text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Icon className="h-3 w-3" />
                {tab.label}
              </button>
            );
          })}
        </div>
        <button
          onClick={closeRightRail}
          className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors duration-fast"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto py-3">
        <Content />
      </div>
    </aside>
  );
}

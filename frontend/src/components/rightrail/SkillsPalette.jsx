import { useState, useEffect } from 'react';
import { API_BASE } from '../../config';
import { Sparkles, ChevronRight } from 'lucide-react';

export default function SkillsPalette() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/chat/skills`, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          setSkills(data);
        }
      } catch {
        // Skills endpoint may not exist yet
      } finally {
        setLoading(false);
      }
    };
    fetchSkills();
  }, []);

  if (loading) {
    return (
      <div className="space-y-2 px-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-10 bg-muted/50 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (skills.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-muted-foreground/50">
        <Sparkles className="h-5 w-5 mb-2" />
        <p className="text-xs">No skills available</p>
        <p className="text-[10px] mt-1">Skills extend what the agent can do</p>
      </div>
    );
  }

  return (
    <div className="space-y-0.5">
      {skills.map((skill) => (
        <button
          key={skill.name || skill.id}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-left hover:bg-muted/50 transition-colors duration-fast group"
        >
          <Sparkles className="h-3.5 w-3.5 text-primary/60 shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-foreground truncate">
              {skill.name}
            </div>
            {skill.description && (
              <div className="text-[10px] text-muted-foreground truncate">
                {skill.description}
              </div>
            )}
          </div>
          <ChevronRight className="h-3 w-3 text-muted-foreground/30 group-hover:text-muted-foreground transition-colors shrink-0" />
        </button>
      ))}
    </div>
  );
}

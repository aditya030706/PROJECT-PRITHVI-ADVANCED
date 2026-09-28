import React, { useEffect, useState } from "react";
import { fetchHierarchyPath } from "../api/hierarchy";

export interface BreadcrumbNode {
  id: string;
  name: string;
  unit_type: string;
  code?: string;
}

interface HierarchyBreadcrumbProps {
  unitId?: string;
  path?: BreadcrumbNode[];
  onSelectNode?: (node: BreadcrumbNode) => void;
  className?: string;
}

export const HierarchyBreadcrumb: React.FC<HierarchyBreadcrumbProps> = ({
  unitId,
  path: externalPath,
  onSelectNode,
  className = "",
}) => {
  const [nodes, setNodes] = useState<BreadcrumbNode[]>(externalPath || []);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (externalPath && externalPath.length > 0) {
      setNodes(externalPath);
      return;
    }
    if (!unitId) return;

    let mounted = true;
    setLoading(true);
    fetchHierarchyPath(unitId)
      .then((res) => {
        if (!mounted) return;
        // res.path is ordered upward: [Mine, Area, Subsidiary, CIL, Ministry]
        // Reverse for left-to-right breadcrumb: Ministry > CIL > Subsidiary > Area > Mine
        const ordered = [...res.path].reverse().map((item) => ({
          id: item.id,
          name: item.name,
          unit_type: item.unit_type,
          code: item.code,
        }));
        setNodes(ordered);
      })
      .catch((err) => {
        console.error("Failed to load hierarchy path:", err);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [unitId, externalPath]);

  if (loading) {
    return (
      <div className={`flex items-center gap-2 py-2 px-3 bg-stone-50 border border-stone-200 rounded text-xs text-stone-500 ${className}`}>
        <span className="inline-block w-2 h-2 rounded-full bg-red-600 animate-ping mr-1"></span>
        Resolving canonical lineage...
      </div>
    );
  }

  if (!nodes || nodes.length === 0) {
    return null;
  }

  const getTypeBadgeColor = (type: string) => {
    switch (type.toUpperCase()) {
      case "MINISTRY":
        return "bg-amber-100 text-amber-900 border-amber-300";
      case "CIL":
        return "bg-red-100 text-red-900 border-red-300 font-semibold";
      case "SUBSIDIARY":
        return "bg-blue-100 text-blue-900 border-blue-300";
      case "AREA":
        return "bg-purple-100 text-purple-900 border-purple-300";
      case "MINE":
        return "bg-emerald-100 text-emerald-900 border-emerald-300";
      default:
        return "bg-stone-100 text-stone-800 border-stone-300";
    }
  };

  return (
    <nav
      aria-label="Organizational Hierarchy Lineage"
      className={`flex items-center flex-wrap gap-1.5 py-2 px-3 bg-white border border-stone-200 rounded shadow-xs text-xs ${className}`}
    >
      <span className="text-[10px] font-bold tracking-wider text-stone-400 uppercase mr-1">
        LINEAGE:
      </span>
      {nodes.map((node, index) => {
        const isLast = index === nodes.length - 1;
        return (
          <React.Fragment key={node.id}>
            <div className="flex items-center gap-1.5">
              <span
                className={`px-1.5 py-0.5 rounded text-[9px] font-mono uppercase tracking-tight border ${getTypeBadgeColor(
                  node.unit_type
                )}`}
              >
                {node.unit_type}
              </span>
              <button
                type="button"
                onClick={() => onSelectNode?.(node)}
                disabled={isLast || !onSelectNode}
                className={`transition-colors text-left ${
                  isLast
                    ? "font-semibold text-stone-900 cursor-default"
                    : onSelectNode
                    ? "text-stone-600 hover:text-red-700 hover:underline cursor-pointer"
                    : "text-stone-600 cursor-default"
                }`}
              >
                {node.name}
              </button>
            </div>
            {!isLast && (
              <span className="text-stone-300 font-bold select-none mx-0.5">
                ›
              </span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

export default HierarchyBreadcrumb;

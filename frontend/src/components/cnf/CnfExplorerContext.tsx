'use client';

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { CNFApiService, type FoodGroup } from '@/lib/api';
import type { UserType } from '@/components/shared/AudienceToggle';
import { loadActiveFoodList, ACTIVE_FOOD_LIST_EVENT } from '@/lib/activeFoodList';

const USER_TYPE_KEY = 'cnf_explorer_user_type_v1';

interface CnfExplorerContextValue {
  userType: UserType;
  setUserType: (next: UserType) => void;
  foodGroups: FoodGroup[];
  groupNameById: Map<number, string>;
  groupIdByName: Map<string, number>;
  groupCountById: Map<number, number>;
  resolveGroupName: (groupId: number, fallback?: string) => string;
  activeFoodCount: number;
  reloadActiveFoodCount: () => void;
}

const CnfExplorerContext = createContext<CnfExplorerContextValue | null>(null);

export function CnfExplorerProvider({ children }: { children: React.ReactNode }) {
  const [userType, setUserTypeState] = useState<UserType>('researcher');
  const [foodGroups, setFoodGroups] = useState<FoodGroup[]>([]);
  const [groupCountById, setGroupCountById] = useState<Map<number, number>>(new Map());
  const [activeFoodCount, setActiveFoodCount] = useState(0);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const stored = window.localStorage.getItem(USER_TYPE_KEY);
    if (stored === 'individual' || stored === 'researcher' || stored === 'policy') {
      setUserTypeState(stored);
    }
  }, []);

  const setUserType = useCallback((next: UserType) => {
    setUserTypeState(next);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(USER_TYPE_KEY, next);
    }
  }, []);

  const reloadActiveFoodCount = useCallback(() => {
    const list = loadActiveFoodList();
    setActiveFoodCount(list?.ingredients.length ?? 0);
  }, []);

  useEffect(() => {
    reloadActiveFoodCount();
    const handler = () => reloadActiveFoodCount();
    window.addEventListener(ACTIVE_FOOD_LIST_EVENT, handler);
    return () => window.removeEventListener(ACTIVE_FOOD_LIST_EVENT, handler);
  }, [reloadActiveFoodCount]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [groups, stats] = await Promise.all([
          CNFApiService.getFoodGroups(),
          CNFApiService.getDatabaseStatistics(),
        ]);
        if (cancelled) return;
        setFoodGroups(groups);
        const counts = new Map<number, number>();
        const nameToId = new Map(groups.map(g => [g.FoodGroupName, g.FoodGroupID]));
        for (const [name, count] of Object.entries(stats.foods_by_group)) {
          const id = nameToId.get(name);
          if (id != null) counts.set(id, count);
        }
        setGroupCountById(counts);
      } catch {
        /* non-blocking */
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const groupNameById = useMemo(
    () => new Map(foodGroups.map(g => [g.FoodGroupID, g.FoodGroupName])),
    [foodGroups],
  );

  const groupIdByName = useMemo(
    () => new Map(foodGroups.map(g => [g.FoodGroupName, g.FoodGroupID])),
    [foodGroups],
  );

  const resolveGroupName = useCallback(
    (groupId: number, fallback?: string) =>
      groupNameById.get(groupId) ?? fallback ?? `Group ${groupId}`,
    [groupNameById],
  );

  const value = useMemo(
    () => ({
      userType,
      setUserType,
      foodGroups,
      groupNameById,
      groupIdByName,
      groupCountById,
      resolveGroupName,
      activeFoodCount,
      reloadActiveFoodCount,
    }),
    [
      userType,
      setUserType,
      foodGroups,
      groupNameById,
      groupIdByName,
      groupCountById,
      resolveGroupName,
      activeFoodCount,
      reloadActiveFoodCount,
    ],
  );

  return (
    <CnfExplorerContext.Provider value={value}>
      {children}
    </CnfExplorerContext.Provider>
  );
}

export function useCnfExplorer(): CnfExplorerContextValue {
  const ctx = useContext(CnfExplorerContext);
  if (!ctx) {
    throw new Error('useCnfExplorer must be used within CnfExplorerProvider');
  }
  return ctx;
}

"use client";

import { useSyncExternalStore } from "react";

type SaveDataConnection = {
  saveData?: boolean;
  addEventListener?: (
    type: string,
    listener: EventListenerOrEventListenerObject,
  ) => void;
};

const subscribers = new Set<() => void>();
let initialized = false;
let allowed = false;

function initializePreferenceStore() {
  if (initialized || typeof window === "undefined") return;
  initialized = true;

  const motionPreference = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  );
  const connection = (
    navigator as Navigator & { connection?: SaveDataConnection }
  ).connection;

  const sync = () => {
    const next = !motionPreference.matches && connection?.saveData !== true;
    if (next === allowed) return;
    allowed = next;
    subscribers.forEach((subscriber) => subscriber());
  };

  motionPreference.addEventListener("change", sync);
  connection?.addEventListener?.("change", sync);
  sync();
}

function subscribe(subscriber: () => void) {
  subscribers.add(subscriber);
  initializePreferenceStore();
  return () => subscribers.delete(subscriber);
}

/**
 * Whether silent, in-view video autoplay is currently appropriate.
 *
 * One external store owns the preference listeners for every player. The
 * server and hydration snapshot stays false, so media remains poster-first;
 * normal visitors opt in immediately after subscription.
 */
export function useVideoAutoplayAllowed(): boolean {
  return useSyncExternalStore(subscribe, () => allowed, () => false);
}

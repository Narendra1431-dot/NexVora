import { createContext } from 'react';
import type { AppStateContextType } from './app-state';

// A separate module keeps context identity stable when the provider hot reloads.
export const AppStateContext = createContext<AppStateContextType | undefined>(undefined);

import { Timestamp } from 'firebase/firestore';

export type UserRole = 'user' | 'admin';

export interface User {
  uid: string;
  email: string | null;
  displayName: string | null;
  role: UserRole;
  createdAt: Timestamp;
  // Add any other user-specific fields here
}

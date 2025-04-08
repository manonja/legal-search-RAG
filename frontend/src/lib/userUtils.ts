// Utility functions for interacting with the Firestore 'users' collection
import { doc, getDoc, collection, getDocs, query, where, updateDoc, deleteDoc, Timestamp } from 'firebase/firestore';
import { db } from './firebase'; // Assuming db is exported from firebase setup
import { User, UserRole } from '@/types/user';

/**
 * Fetches a single user document by UID.
 * @param uid The user's unique identifier.
 * @returns The user data or null if not found.
 */
export const getUserById = async (uid: string): Promise<User | null> => {
  if (!uid) return null;
  try {
    const userDocRef = doc(db, 'users', uid);
    const userDocSnap = await getDoc(userDocRef);

    if (userDocSnap.exists()) {
      // Ensure correct typing, especially for Timestamps
      const userData = userDocSnap.data() as User;
      // You might need manual timestamp conversion if Firestore returns server format
      // e.g., if (userData.createdAt && !(userData.createdAt instanceof Timestamp)) {
      //   userData.createdAt = (userData.createdAt as any).toDate();
      // }
      return userData;
    } else {
      console.log(`No user found with UID: ${uid}`);
      return null;
    }
  } catch (error) {
    console.error("Error fetching user by ID:", error);
    throw new Error('Failed to fetch user data.'); // Re-throw or handle as needed
  }
};

// --- Placeholder for other functions ---

/**
 * Fetches all user documents.
 * @returns An array of user data.
 */
export const getAllUsers = async (): Promise<User[]> => {
  try {
    const usersCollectionRef = collection(db, 'users');
    const querySnapshot = await getDocs(usersCollectionRef);

    const users: User[] = [];
    querySnapshot.forEach((doc) => {
      // Ensure correct typing, handle potential timestamp conversion if needed
      users.push(doc.data() as User);
    });

    return users;
  } catch (error) {
    console.error("Error fetching all users:", error);
    throw new Error('Failed to fetch all users.');
  }
};

/**
 * Fetches users by their assigned role.
 * @param role The role to filter by ('user' or 'admin').
 * @returns An array of user data matching the role.
 */
export const getUsersByRole = async (role: UserRole): Promise<User[]> => {
  try {
    const usersCollectionRef = collection(db, 'users');
    const q = query(usersCollectionRef, where("role", "==", role));
    const querySnapshot = await getDocs(q);

    const users: User[] = [];
    querySnapshot.forEach((doc) => {
      users.push(doc.data() as User);
    });

    return users;
  } catch (error) {
    console.error(`Error fetching users by role (${role}):`, error);
    throw new Error(`Failed to fetch users with role ${role}.`);
  }
};

/**
 * Updates the role of a specific user.
 * @param uid The UID of the user to update.
 * @param role The new role to assign.
 */
export const updateUserRole = async (uid: string, role: UserRole): Promise<void> => {
  if (!uid) {
    console.error("updateUserRole requires a valid UID.");
    throw new Error("Invalid UID provided for role update.");
  }
  try {
    const userDocRef = doc(db, 'users', uid);
    await updateDoc(userDocRef, { role: role }); // Update only the role field
    console.log(`Successfully updated role to ${role} for user ${uid}`);
  } catch (error) {
    console.error(`Error updating role for user ${uid}:`, error);
    throw new Error('Failed to update user role.');
  }
};

/**
 * Deletes a user document from Firestore (does not delete the Auth user).
 * @param uid The UID of the user document to delete.
 */
export const deleteUserDocument = async (uid: string): Promise<void> => {
  if (!uid) {
    console.error("deleteUserDocument requires a valid UID.");
    throw new Error("Invalid UID provided for document deletion.");
  }
  try {
    const userDocRef = doc(db, 'users', uid);
    await deleteDoc(userDocRef);
    console.log(`Successfully deleted Firestore document for user ${uid}`);
  } catch (error) {
    console.error(`Error deleting Firestore document for user ${uid}:`, error);
    throw new Error('Failed to delete user document.');
  }
};

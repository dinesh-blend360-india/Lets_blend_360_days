# Assignment Board (HTML, CSS, JavaScript + Firebase)

A small three-page assignment-link sharing app:

- `index.html` — public assignment board; people can expand a name to browse sections and links.
- `login.html` — email/password sign-in, account creation, and password-reset email.
- `support.html` — saves support requests as Firestore documents.

Users can view everyone's assignment links, but only a signed-in user can edit the profile whose document ID matches their Firebase Auth UID. Passwords are handled by Firebase Authentication; this app does **not** save plaintext passwords.

## 1. Create and configure Firebase

1. Open the [Firebase Console](https://console.firebase.google.com/) and create a project.
2. In **Build → Authentication → Sign-in method**, enable **Email/Password**.
3. In **Build → Firestore Database**, create a database.
4. In **Project settings → General → Your apps**, add a Web app and copy its Firebase web configuration.
5. Copy `.env.example` to `.env.local` and fill in the values:

   ```env
   VITE_FIREBASE_API_KEY=...
   VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your-project
   VITE_FIREBASE_STORAGE_BUCKET=...
   VITE_FIREBASE_MESSAGING_SENDER_ID=...
   VITE_FIREBASE_APP_ID=...
   ```

   Firebase web configuration is designed to be present in a browser. Do not add a service-account private key or Admin SDK secret to this project. The actual access controls are enforced by Firestore Security Rules.

6. Publish the rules from `firestore.rules` in **Firestore Database → Rules**. Or, after installing Firebase CLI and selecting your project, run:

   ```bash
   firebase deploy --only firestore:rules
   ```

## 2. Run locally

Install Node.js 20.19+ or 22.12+ and then run from this folder:

```bash
npm install
npm run dev
```

Vite prints a local URL, usually `http://localhost:5173`. Open it in your browser. To build the static pages:

```bash
npm run build
npm run preview
```

## 3. Deploy to Firebase Hosting (optional)

After completing Firebase CLI setup and creating `.env.local`, run:

```bash
npm install -g firebase-tools
firebase login
firebase use --add
npm run build
firebase deploy
```

Choose the Firebase project that owns your Firestore database. The provided `firebase.json` deploys the `dist/` folder and `firestore.rules`.

## Firestore data model

- `assignments/{firebaseAuthUid}` — `{ displayName, sections: [{ title, links: [{ label, url }] }], updatedAt }`
- `supportTickets/{autoId}` — `{ name, email, message, createdAt }`

The assignment list is public by design. Only the owner can write their assignment document. Support tickets can be created from the client but cannot be read, changed, or deleted by the client. An admin workflow can be added later with a trusted server-side environment.

## Before sharing publicly

- Test with two different accounts: confirm that each user can edit only their own profile.
- Use Firestore's Rules Playground or Emulator Suite to test access-control behavior.
- Consider Firebase App Check and server-side rate limiting for support tickets to limit automated spam.
- Use only links you're comfortable making visible to everyone who can open the board.

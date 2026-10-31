# Connect My Booking 360 to Google (one-off, about 15 minutes)

The GitHub Pages version of My Booking 360 signs in with your Google account. It uses:

- **Google Drive**: a private, hidden app-data file holds your bookings, clients, quotes, invoices and settings. Only this app can see it; it doesn't appear in your Drive file list.
- **Google Calendar**: bookings appear on your main calendar in their status colours.
- **Gmail**: quotes, invoices and reminders send from your own address.

Google needs a **client ID** for the app. You create it once in Google Cloud. It's free.

## 1. Create a Google Cloud project
1. Go to <https://console.cloud.google.com/> and sign in with the Google account you'll use for bookings.
2. Click the project picker at the top, then **New project**. Name it `My Booking 360` and click **Create**. Make sure it's selected.

## 2. Turn on the three Google APIs
Go to **APIs & Services → Library**, search for each of these, open it and click **Enable**:
- **Google Drive API**
- **Google Calendar API**
- **Gmail API**

## 3. Set up the consent screen
1. Go to **APIs & Services → OAuth consent screen** (it may be called **Google Auth Platform**). Click **Get started**.
2. **App name**: `My Booking 360`. **User support email**: your email. Click **Next**.
3. **Audience**: choose **External**. Click **Next**.
4. **Contact information**: your email. Click **Next**, agree to the policy, then **Create**.
5. Open **Audience**, and under **Test users** click **Add users**. Add your own Gmail address and save.
   Leave the app in **Testing**. That's right for your own use.

## 4. Create the client ID
1. Go to **APIs & Services → Credentials** (or **Clients**). Click **Create credentials → OAuth client ID** (or **Create client**).
2. **Application type**: **Web application**. **Name**: `My Booking 360`.
3. Under **Authorized JavaScript origins**, click **Add URI** and enter:
   ```
   https://teatea007.github.io
   ```
4. Under **Authorized redirect URIs**, click **Add URI** and enter exactly (with the slash at the end):
   ```
   https://teatea007.github.io/Job-Bookings-App/
   ```
5. Click **Create**. Copy the **Client ID**. It ends in `.apps.googleusercontent.com`.
   You don't need the client secret.

## 5. Put the client ID in the app
Either:
- **Send the client ID to Claude**, and it will be added to `config.js` so every device picks it up automatically. The client ID isn't a password: Google only accepts it from the addresses above. Or:
- Open the app, paste it on the **Connect your Google account** screen and tap **Continue**. It's saved on that device only, so you'd repeat this on each device.

## 6. Sign in
Tap **Sign in with Google** and choose your account.

- Google will say **"Google hasn't verified this app"**. That's expected for a personal app in Testing. Tap **Continue**.
- Tick all the boxes on the permissions screen (Drive app data, Calendar events, Gmail drafts/send) and tap **Continue**.

While the app is in Testing, Google may ask you to approve it again from time to time. Just sign in again; your data stays in Drive.

## Add it to your home screen
- **iPhone**: open <https://teatea007.github.io/Job-Bookings-App/> in **Safari** → **Share** → **Add to Home Screen**. It opens full screen with no browser bars.
- **Mac**: in Safari, **File → Add to Dock**. In Chrome, the install icon in the address bar.

## Moving data from the claude.ai version
Ask Claude to export your bookings from the claude.ai app into a backup file. Then, in the new app, go to **Settings → Restore from a file** and pick that file.

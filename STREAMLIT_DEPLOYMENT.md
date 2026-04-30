# 🚀 Deploy to Streamlit Cloud (FREE)

This guide will help you deploy your NorthLadder Data-Quality Detection app to Streamlit Cloud for **FREE** so you can share it with colleagues.

## ✅ Prerequisites

- GitHub account
- This repository pushed to GitHub (✅ Already done!)

---

## 📝 Step-by-Step Deployment

### Step 1: Go to Streamlit Cloud

Visit: **[share.streamlit.io](https://share.streamlit.io)**

### Step 2: Sign In

Click **"Sign in with GitHub"** and authorize Streamlit to access your repositories.

### Step 3: Create New App

1. Click the **"New app"** button
2. You'll see a form with three fields:

### Step 4: Fill in the Details

**Repository:**
```
dharmik515/North-ladder-balcbelt-vs-backend-
```

**Branch:**
```
main
```

**Main file path:**
```
streamlit_app.py
```

### Step 5: Advanced Settings (Optional)

Click **"Advanced settings"** if you want to:
- Set a custom subdomain
- Add secrets/environment variables
- Configure Python version

For this app, **default settings work perfectly!**

### Step 6: Deploy!

Click the **"Deploy!"** button.

Streamlit will:
1. ✅ Clone your repository
2. ✅ Install dependencies from `requirements.txt`
3. ✅ Start your app
4. ✅ Give you a public URL

**Deployment takes 2-3 minutes.**

---

## 🎉 Your App is Live!

Once deployed, you'll get a URL like:

```
https://your-app-name.streamlit.app
```

### Share with Colleagues

Just send them the URL! They can:
- ✅ Upload files
- ✅ Run analysis
- ✅ Download reports
- ✅ No login required

---

## 🔄 Auto-Updates

Every time you push to GitHub, Streamlit Cloud will:
- ✅ Automatically detect changes
- ✅ Redeploy your app
- ✅ Keep the same URL

**No manual redeployment needed!**

---

## 📊 Monitor Your App

From the Streamlit Cloud dashboard, you can:
- View app logs
- See usage statistics
- Restart the app
- Manage settings

---

## 🆓 Free Tier Limits

Streamlit Cloud FREE tier includes:
- ✅ **Unlimited public apps**
- ✅ **1 GB RAM per app**
- ✅ **1 CPU core**
- ✅ **No time limits**
- ✅ **No credit card required**

**Perfect for internal company tools!**

---

## 🐛 Troubleshooting

### App Won't Start?

1. Check the logs in Streamlit Cloud dashboard
2. Verify `requirements.txt` has all dependencies
3. Make sure `streamlit_app.py` is in the root directory

### Upload Fails?

- Max file size: 200 MB (configurable in `.streamlit/config.toml`)
- Supported formats: `.xlsx` only

### Slow Performance?

- Free tier has 1 GB RAM
- Large files (10,000+ rows) may take 2-3 minutes
- Consider upgrading to Streamlit Cloud Pro if needed

---

## 🔒 Security Notes

### Public vs Private Apps

**Free tier = Public apps** (anyone with the URL can access)

For **private apps** (password-protected):
- Upgrade to Streamlit Cloud Pro ($20/month)
- Or deploy on your own server using `app.py` (FastAPI version)

### Data Privacy

- Files are processed in-memory
- No data is stored permanently
- Each session is isolated
- Files are deleted after processing

---

## 💡 Tips

### Custom Domain

Want `quality-check.yourcompany.com` instead of `.streamlit.app`?
- Available on Streamlit Cloud Pro plan
- Or use the FastAPI version with your own hosting

### Multiple Environments

Deploy multiple versions:
- **Production:** `main` branch → `https://northladder-prod.streamlit.app`
- **Testing:** `dev` branch → `https://northladder-dev.streamlit.app`

### Secrets Management

If you need API keys or passwords:
1. Go to app settings in Streamlit Cloud
2. Add secrets in TOML format
3. Access via `st.secrets` in your code

---

## 🎯 Next Steps

1. ✅ Deploy to Streamlit Cloud
2. ✅ Share URL with your team
3. ✅ Collect feedback
4. ✅ Push updates to GitHub (auto-deploys!)

---

## 📞 Need Help?

- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io)
- **Community Forum:** [discuss.streamlit.io](https://discuss.streamlit.io)
- **GitHub Issues:** Report bugs in this repository

---

## 🚀 Ready to Deploy?

Go to **[share.streamlit.io](https://share.streamlit.io)** and follow the steps above!

Your colleagues will thank you! 🎉

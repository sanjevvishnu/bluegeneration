# 🎤 AI Interview Practice - Next.js App

A modern, responsive Next.js application for practicing technical interviews with AI-powered interviewers using NextUI components.

## ✨ Features

- 🎨 **Modern UI**: Built with NextUI and Tailwind CSS
- 🌓 **Dark/Light Mode**: Automatic theme switching
- 📱 **Responsive Design**: Works on desktop and mobile
- 🎯 **Multiple Interview Modes**: Google, Microsoft, Amazon, Startup, General
- 🎤 **Real-time Audio**: WebSocket connection to Python backend
- 🔊 **Audio Visualization**: Live audio level monitoring
- ⚡ **Fast Loading**: Optimized with Next.js 14

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
# or
yarn install
```

### 2. Start Development Server
```bash
npm run dev
# or
yarn dev
```

### 3. Start WebSocket Backend
```bash
# In a separate terminal
python websocket_server.py
```

### 4. Open App
Navigate to [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
src/
├── app/
│   ├── layout.tsx          # Root layout with NextUI provider
│   ├── page.tsx            # Home page (interview mode selection)
│   ├── interview/
│   │   └── page.tsx        # Interview conversation page
│   └── globals.css         # Global styles with Tailwind
public/
└── prompts.json           # Interview prompts data
```

## 🎯 How It Works

1. **Home Page** (`/`): Select interview mode from dropdown
2. **Interview Page** (`/interview?prompt=mode`): Real-time voice conversation
3. **WebSocket Connection**: Connects to Python backend on port 8765
4. **Audio Processing**: Same PCM audio pipeline as vanilla HTML version

## 🛠️ Components Used

### NextUI Components
- `Card`, `CardBody`, `CardHeader` - Layout containers
- `Button` - Interactive elements
- `Select`, `SelectItem` - Dropdown selection
- `Chip` - Status indicators
- `Progress` - Audio level visualization
- `Divider` - Visual separators

### React Icons
- Material Design icons for intuitive interface

## 🎨 Styling

- **Tailwind CSS**: Utility-first CSS framework
- **NextUI**: Beautiful React components
- **Custom Gradients**: Beautiful background gradients
- **Responsive Grid**: Mobile-first design

## 🔧 Configuration

### tailwind.config.js
- NextUI theme integration
- Custom color schemes for light/dark modes
- Extended utilities for gradients

### next.config.js
- App directory enabled
- Static file serving for prompts.json

## 📦 Build & Deploy

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm start
```

### Static Export (Optional)
```bash
npm run build
# Add "output: 'export'" to next.config.js for static hosting
```

## 🔌 Backend Integration

The Next.js frontend connects to the same Python WebSocket server:

```python
# websocket_server.py should be running on port 8765
python websocket_server.py
```

The app automatically:
1. Loads prompts from `/public/prompts.json`
2. Connects to `ws://localhost:8765`
3. Sends prompt selection to backend
4. Streams audio bidirectionally

## 🎯 Interview Modes

Each mode has:
- **Unique personality**: Tailored system instructions
- **Company-specific focus**: Relevant technical areas
- **Visual identity**: Custom icons and colors

### Available Modes:
- 🏢 **Microsoft**: Professional, comprehensive technical evaluation
- 🔍 **Google**: Algorithm-focused with optimization challenges
- 📦 **Amazon**: Technical + Leadership Principles
- 💡 **Startup**: Versatile full-stack problem-solving
- 📚 **General**: Comprehensive interview preparation

## 💡 Tips

- **Use headphones** to prevent audio feedback
- **Allow microphone access** when prompted
- **Stable internet** for smooth WebSocket connection
- **Modern browser** for best Web Audio API support

## 🔍 Troubleshooting

**Next.js not starting?**
- Run `npm install` to ensure dependencies
- Check Node.js version (16+ recommended)

**Prompts not loading?**
- Ensure `public/prompts.json` exists
- Check browser console for fetch errors

**Audio not working?**
- Verify WebSocket server is running
- Check microphone permissions
- Use Chrome/Firefox for best compatibility

---

**Built with ❤️ using Next.js 14 + NextUI + Tailwind CSS** 🚀 
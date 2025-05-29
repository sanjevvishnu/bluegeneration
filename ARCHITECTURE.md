# AI Interview Practice App v2 - Architecture Guide

## 🏗️ Clean Architecture Overview

This is a complete rewrite of the AI Interview Practice app with a focus on **clean code**, **maintainability**, and **scalability**. The new architecture follows modern React/Next.js best practices.

## 📁 Folder Structure

```
interview-app-v2/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx           # Main home page
│   │   ├── layout.tsx         # Root layout with metadata
│   │   └── globals.css        # Global styles
│   │
│   ├── components/
│   │   ├── ui/                # Reusable UI primitives
│   │   │   ├── button.tsx     # Button component with variants
│   │   │   ├── card.tsx       # Card component family
│   │   │   └── badge.tsx      # Badge component with colors
│   │   │
│   │   └── features/          # Feature-specific components
│   │       ├── InterviewCard.tsx    # Interview prompt display
│   │       └── InterviewSession.tsx # Interview session manager
│   │
│   ├── hooks/                 # Custom React hooks
│   │   └── useWebSocket.ts    # WebSocket connection management
│   │
│   ├── lib/                   # Utility libraries
│   │   └── utils.ts           # Common utility functions
│   │
│   ├── types/                 # TypeScript type definitions
│   │   └── interview.ts       # Interview-related types
│   │
│   └── constants/             # App constants
│       └── prompts.ts         # Interview prompt configurations
│
├── package.json               # Dependencies and scripts
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.js        # Tailwind CSS configuration
├── README.md                 # Project documentation
└── ARCHITECTURE.md           # This file
```

## 🎯 Design Principles

### 1. **Single Responsibility Principle**
- Each component has one clear purpose
- UI components are separate from business logic
- Hooks encapsulate specific functionality

### 2. **Composition over Inheritance**
- Components are built using composition
- Reusable UI primitives in `components/ui/`
- Feature components combine UI primitives

### 3. **Type Safety First**
- Comprehensive TypeScript types
- Strict type checking enabled
- Interface-driven development

### 4. **Separation of Concerns**
- UI components in `components/`
- Business logic in `hooks/`
- Types in `types/`
- Constants in `constants/`

## 🧩 Component Architecture

### UI Components (`src/components/ui/`)

**Purpose**: Reusable, unstyled components that can be used throughout the app.

```typescript
// Example: Button component with variants
<Button variant="default" size="lg">
  Start Interview
</Button>

<Button variant="outline" size="icon">
  <MicIcon />
</Button>
```

**Key Features**:
- Built with Radix UI primitives
- Styled with Tailwind CSS
- Variant-based styling using `class-variance-authority`
- Fully accessible by default

### Feature Components (`src/components/features/`)

**Purpose**: Business logic components that combine UI primitives for specific features.

```typescript
// InterviewCard: Displays interview information
<InterviewCard 
  prompt={prompt} 
  onStart={handleStart}
  isLoading={loading}
/>

// InterviewSession: Manages interview flow
<InterviewSession 
  prompt={currentPrompt}
  onEnd={handleEnd}
/>
```

**Key Features**:
- Encapsulate feature-specific logic
- Use UI components for presentation
- Handle user interactions
- Manage local state

## 🔗 Custom Hooks

### `useWebSocket` Hook

**Purpose**: Manages WebSocket connections with automatic reconnection and error handling.

```typescript
const { isConnected, sendMessage, error } = useWebSocket({
  url: 'ws://localhost:8765',
  onMessage: handleMessage,
  onError: handleError
})
```

**Features**:
- Automatic reconnection with exponential backoff
- Connection state management
- Error handling and reporting
- Message queuing and sending

## 📊 Type System

### Core Types (`src/types/interview.ts`)

```typescript
interface InterviewPrompt {
  id: string
  name: string
  company: string
  description: string
  systemInstruction: string
  difficulty: 'junior' | 'mid' | 'senior'
  type: 'technical' | 'behavioral' | 'system-design'
  duration: number
}

interface InterviewSession {
  id: string
  promptId: string
  startTime: Date
  endTime?: Date
  status: 'waiting' | 'connecting' | 'active' | 'completed'
  transcript: TranscriptEntry[]
}
```

**Benefits**:
- Compile-time type checking
- IntelliSense support
- Refactoring safety
- Documentation through types

## 🎨 Styling Architecture

### Tailwind CSS + CSS Variables

```css
/* globals.css */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  /* ... */
}
```

**Benefits**:
- Consistent design system
- Easy theme switching
- Utility-first approach
- Responsive design built-in

## 🔄 Data Flow

### 1. **Component State Flow**
```
HomePage → InterviewCard → onClick → InterviewSession
```

### 2. **WebSocket Communication**
```
InterviewSession → useWebSocket → WebSocket Server → AI Backend
```

### 3. **Type Safety Flow**
```
Constants → Types → Components → Runtime
```

## 🚀 Performance Optimizations

### 1. **Code Splitting**
- Automatic route-based splitting with Next.js
- Dynamic imports for heavy components
- Lazy loading of non-critical features

### 2. **Memoization**
- `useCallback` for event handlers
- `useMemo` for expensive calculations
- React.memo for pure components

### 3. **Bundle Optimization**
- Tree shaking enabled
- Minimal dependencies
- Optimized build output

## 🧪 Testing Strategy

### Component Testing
```typescript
// Example test structure
describe('InterviewCard', () => {
  it('displays prompt information correctly', () => {
    // Test implementation
  })
  
  it('calls onStart when button is clicked', () => {
    // Test implementation
  })
})
```

### Hook Testing
```typescript
describe('useWebSocket', () => {
  it('connects to WebSocket server', () => {
    // Test implementation
  })
  
  it('handles connection errors gracefully', () => {
    // Test implementation
  })
})
```

## 📈 Scalability Considerations

### 1. **Adding New Features**
- Create new components in appropriate folders
- Define types first
- Use existing UI components
- Follow established patterns

### 2. **State Management**
- Currently using React hooks
- Easy to migrate to Zustand/Redux if needed
- State is co-located with components

### 3. **API Integration**
- WebSocket abstracted in custom hook
- Easy to add REST API calls
- Type-safe API responses

## 🔧 Development Workflow

### 1. **Adding a New Component**
```bash
# 1. Create the component file
touch src/components/ui/new-component.tsx

# 2. Define types if needed
# Add to src/types/

# 3. Create tests
touch src/components/ui/__tests__/new-component.test.tsx

# 4. Export from index
# Add to src/components/ui/index.ts
```

### 2. **Adding a New Feature**
```bash
# 1. Create feature component
touch src/components/features/NewFeature.tsx

# 2. Add types
# Update src/types/

# 3. Add constants if needed
# Update src/constants/

# 4. Create custom hook if needed
touch src/hooks/useNewFeature.ts
```

## 🎯 Key Benefits of This Architecture

1. **Maintainability**: Clear separation of concerns makes code easy to understand and modify
2. **Reusability**: UI components can be reused across different features
3. **Type Safety**: Comprehensive TypeScript prevents runtime errors
4. **Testability**: Components and hooks are easy to test in isolation
5. **Scalability**: Architecture supports growth without major refactoring
6. **Developer Experience**: Great IntelliSense, debugging, and tooling support

## 🔮 Future Enhancements

### Planned Improvements
- [ ] Add Storybook for component documentation
- [ ] Implement comprehensive testing suite
- [ ] Add state management (Zustand)
- [ ] Create design system documentation
- [ ] Add performance monitoring
- [ ] Implement error boundaries
- [ ] Add internationalization support

This architecture provides a solid foundation for building a scalable, maintainable AI interview practice application. 
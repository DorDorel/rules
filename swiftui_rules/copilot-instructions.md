# iOS Project Rules — SwiftUI, Intents & Architecture

> For Claude Code: Be strict at boundaries. Pragmatic everywhere else.

---

## 1. Role & Persona

Senior iOS Architect writing scalable Swift code for iOS 17+.
Guard against spaghetti code and architectural drift.

**Stack:**
- iOS 17+ | Swift 6.2+
- SwiftUI + Observation
- Structured Concurrency

---

## 2. Operating Modes (Context-Aware Strictness)

### UI Mode (Default)
- Regular SwiftUI views
- Screens, forms, lists
- Flexible, pragmatic

### Intent-Strict Mode
Activated when code involves:
- AppIntent / SnippetIntent
- Spotlight, Shortcuts, Siri
- System-facing boundaries

**Rule:** Strictness by context, not ideology.

---

## 3. Architecture

### Structure
```
App/
├── Features/[Feature]/
│   ├── Domain/        // protocols, models
│   ├── Data/          // implementations
│   └── Presentation/  // SwiftUI + VMs
├── Core/
└── AppEntry.swift
```

### Boundaries
- Domain is pure
- Data implements contracts
- Presentation is UI-only

---

## 4. Contract-First Development (MANDATORY)

**Critical Rule:** Every feature capability MUST start with a Domain protocol definition.

### Two-Step Process

**Step 1: Protocol Design (SHOW FIRST)**
- Define the protocol signature in Domain layer
- Include all method signatures with typed throws
- Document expected behavior
- **WAIT for approval before implementing**

**Step 2: Implementation (AFTER APPROVAL)**
- Implement concrete service in Data layer
- Inject via initializer into ViewModel
- Create protocol-based mock for tests

### Why This Matters
1. **Human Review:** Developer reviews the contract before implementation
2. **Testability:** Protocol enables easy mocking
3. **Flexibility:** Implementation can change without breaking dependents
4. **Clarity:** Forces explicit definition of capabilities

### Example Flow

```swift
// STEP 1: Show this first and wait
// Domain/AuthService.swift
protocol AuthService: Sendable {
    func login(email: String, password: String) async throws(AuthError) -> User
    func logout() async throws(AuthError)
}

enum AuthError: Error {
    case invalidCredentials
    case networkFailure
}
```

```swift
// STEP 2: Only after approval
// Data/FirebaseAuthService.swift
struct FirebaseAuthService: AuthService {
    func login(email: String, password: String) async throws(AuthError) -> User {
        // Implementation
    }
}
```

```swift
// Presentation/LoginViewModel.swift
@MainActor
@Observable
final class LoginViewModel {
    private let authService: any AuthService  // Injected
    
    init(authService: any AuthService) {
        self.authService = authService
    }
}
```

### Exceptions
- Pure value types (no I/O)
- Trivial helpers with no business logic

---

## 5. State Management

### Observation
- `@Observable` for ViewModels
- No `ObservableObject`

### Property Wrappers
| Wrapper | Use |
|---------|-----|
| `@State` | View owns state |
| `@Binding` | Child mutates parent |
| `@Bindable` | Bindings to `@Observable` |

### ViewState
- Use `enum State` for async/exclusive phases
- Avoid boolean soup
- Don't force enums for trivial UI

---

## 6. SwiftUI Rules

- Small, pure `body`
- No business logic in views
- Extract subviews early
- Use stable identity in lists
- Prefer modifiers over conditionals

### Modern APIs
- `NavigationStack` (not `NavigationView`)
- `foregroundStyle()` (not `foregroundColor()`)
- `.clipShape(.rect(cornerRadius:))`
- `.sheet(item:)` for model-driven sheets

---

## 7. Swift Concurrency (Essential Only)

### Swift 6.2 Patterns
- **Typed Throws:** Use `throws(SpecificError)` in Domain/Data
- **@concurrent:** For CPU-intensive work that must not block actor
  ```swift
  nonisolated struct ImageProcessor {
      @concurrent func process(_ data: Data) -> Image { ... }
  }
  ```
- **Isolated Conformances:** Apply `@MainActor` to protocol conformances
  ```swift
  extension ViewModel: @MainActor Exportable { ... }
  ```

### UI Integration
- Use `.task` for async work
- Respect `Task.isCancelled`
- ViewModels are `@MainActor`

---

## 8. Network Layer (Mandatory Pattern)

Never call `URLSession.shared.data()` directly.

**Required:**
```swift
actor NetworkManager {
    func fetch<T: Decodable>(url: URL) async throws(NetworkError) -> T {
        // Centralized decoding + error handling
    }
}
```

**Benefits:**
- Single decoder config
- Consistent error mapping
- Auth header injection

---

## 9. SwiftData (When Used)

### Inheritance
- Use for true IS-A relationships
- `@Model` on base class
- Keep hierarchy shallow

### Queries
```swift
// Polymorphic
@Query var trips: [Trip]  // includes subclasses

// Filtered
#Predicate<Trip> { $0 is BusinessTrip }
```

---

## 10. Intent-Strict Rules (When Applicable)

### Intents
- Minimal, predictable inputs
- Clear success/failure outputs
- No UI logic

### Snippets
- Standalone understandable
- No navigation
- Compact UI (< 340pt)
- Optimistic only when safe

---

## 11. Foundation Models (@Generable)

When using Apple Intelligence:

### Availability
```swift
switch SystemLanguageModel.default.availability {
case .deviceNotEligible: // Handle
case .modelNotReady: // Handle
}
```

### Structured Data
- Access via `response.content` (NOT `.output`)
- Use `@Guide` for constraints
- Stream with `PartiallyGenerated<T>`

### Session Management
- Reuse session for multi-turn
- Monitor 4,096 token limit
- Reset on `exceededContextWindowSize`

---

## 12. Accessibility (Mandatory)

- Accessibility labels on interactive elements
- Dynamic Type support
- Respect Reduce Motion
- WCAG AA contrast

---

## 13. Performance

### Profile When
- View init > 100ms
- Scroll drops below 60fps
- SwiftData query > 200ms

### Patterns
```swift
// Bad - recreates formatter
Text(date, formatter: DateFormatter())

// Good - reuse
private let formatter: DateFormatter = { ... }()
```

---

## 14. Testing

- **Framework:** Swift Testing (`import Testing`)
- Mock via Domain protocols
- In-memory `ModelContainer` for SwiftData
- Test `ViewState` transitions

---

## 15. Anti-Patterns (Forbidden)

- Boolean state hell (`isLoading`, `isError` separately)
- Logic in View `body`
- Force unwrap (except tests)
- `@Published` with Observation
- Stateful services as classes
- Parsing `response.output` with `@Generable`

---

## 16. Agent Conduct (Meta Rules)

**Do NOT:**
- Apply formatting/linting
- Reorder properties/files
- Enforce architectures beyond this doc

**Communication:**
- "suggest" / "consider" for optimizations
- "must" / "never" only for correctness

**When uncertain:** Exclude guidance.

---

### Contract-First Workflow (STRICT)

When implementing a new feature:

1. **ALWAYS present the protocol definition FIRST**
2. Say: "Here's the proposed protocol. Should I proceed with implementation?"
3. **WAIT** for human approval
4. Only then implement the concrete service
5. Show injection into ViewModel last

**Never skip the protocol review step.**

---

## Philosophy

- Contracts over concreteness
- Boundaries over convenience
- Intents over screens
- Pragmatism over dogma

**Strict where it matters. Flexible where it doesn't.**
# iOS Project Rules — SwiftUI, Intents & Architecture

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

### Protocol Design Guidelines

A good protocol:
- **Minimal surface:** Only essential methods
- **Clear semantics:** No ambiguous method names
- **Explicit errors:** All failure modes in typed throws enum
- **No leaky abstractions:** No implementation details in signature
- **Future-proof:** Easy to extend without breaking changes

**Example of GOOD protocol:**
```swift
protocol PaymentService: Sendable {
    func process(
        amount: Decimal,
        method: PaymentMethod
    ) async throws(PaymentError) -> Transaction
}

enum PaymentError: Error {
    case insufficientFunds
    case invalidPaymentMethod
    case networkFailure
    case timeout
    case rateLimited(retryAfter: TimeInterval)
}
```

**Example of BAD protocol:**
```swift
protocol PaymentService {
    // ❌ Too many methods
    func validateCard() -> Bool
    func chargeCard() -> String
    func getStripeClient() -> StripeClient  // ❌ Leaky abstraction
    func process() throws -> Any  // ❌ Untyped errors, Any return
}
```

### Why This Matters
1. **Human Review:** Developer reviews the contract before implementation
2. **Testability:** Protocol enables easy mocking
3. **Flexibility:** Implementation can change without breaking dependents
4. **Clarity:** Forces explicit definition of capabilities

### Exceptions
- Pure value types (no I/O)
- Trivial helpers with no business logic

---

## 5. State Management

### Observation
- `@Observable` for ViewModels
- No `ObservableObject`

### Property Wrappers (Critical Rules)

| Wrapper | Use When | Example |
|---------|----------|---------|
| `@State` | View **owns** the state | `@State private var count = 0` |
| `@Binding` | Child mutates parent state | `@Binding var isOn: Bool` |
| `@Bindable` | Need bindings to injected `@Observable` | `@Bindable var viewModel: VM` |
| `let` | Read-only injected value | `let viewModel: VM` |

**CRITICAL:** Never mark injected or passed-in values as `@State`

```swift
// ❌ WRONG - State wrapper on injected dependency
struct ProfileView: View {
    @State private var viewModel: ProfileViewModel
    
    init(viewModel: ProfileViewModel) {
        self._viewModel = State(initialValue: viewModel)  // NO!
    }
}

// ✅ CORRECT - Let for read-only
struct ProfileView: View {
    let viewModel: ProfileViewModel
}

// ✅ CORRECT - Bindable when you need two-way binding
struct ProfileView: View {
    @Bindable var viewModel: ProfileViewModel
}
```

**Why this matters:**
- `@State` means "this view owns and manages this value"
- Injected dependencies are owned by the parent
- Wrapping injection in `@State` creates lifecycle confusion
- Can cause retain cycles and testing issues

**Rule of thumb:** If it comes through `init()`, it's NOT `@State`

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

## 8. Network Layer (Conditional)

**When to use centralized NetworkManager:**
- Multiple features make network calls
- Shared authentication/headers needed
- Consistent error handling across app
- Complex request/response pipeline

**When URLSession.shared is acceptable:**
- Simple AppIntents with one-off requests
- Prototype/testing code
- Single isolated network call with no shared config

### Centralized Pattern (Multi-Feature Apps)

Never call `URLSession.shared.data()` directly in feature code.

**Required:**
```swift
actor NetworkManager {
    static let shared = NetworkManager()
    
    func fetch<T: Decodable>(url: URL) async throws(NetworkError) -> T {
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.serverError
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
}

enum NetworkError: Error {
    case serverError
    case decodingFailed
    case unauthorized
}
```

**Benefits:**
- Single decoder configuration
- Consistent error mapping
- Auth header injection point
- Request/response logging

### Simple Pattern (AppIntents, Prototypes)

Direct URLSession is acceptable when:
- No shared configuration needed
- One-off operation
- No cross-feature consistency required

```swift
struct FetchDataIntent: AppIntent {
    func perform() async throws -> String {
        let (data, _) = try await URLSession.shared.data(from: url)
        return String(data: data, encoding: .utf8) ?? ""
    }
}
```

### Migration Trigger

**Introduce NetworkManager when:**
- 3+ network call sites exist
- Need shared headers (auth tokens)
- Same decoder config repeated
- Error handling duplicated

**Refactoring is straightforward:**
```swift
// Before: Scattered calls
let (data, _) = try await URLSession.shared.data(from: url)
let result = try JSONDecoder().decode(T.self, from: data)

// After: Centralized
let result: T = try await NetworkManager.shared.fetch(url: url)
```

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

## 15. Anti-Patterns (FORBIDDEN)

These patterns are **strictly forbidden** and will cause issues:

### State Management
- ❌ **Boolean state hell:** Separate `isLoading`, `isError`, `isSuccess` flags
  - ✅ Use: `enum State { case loading, success, error }`
- ❌ **@State on injected values:** `@State private var viewModel: VM` in init
  - ✅ Use: `let viewModel: VM` or `@Bindable var viewModel: VM`
- ❌ **@Published with Observation:** Mixing old and new frameworks
  - ✅ Use: `@Observable` only

### Architecture
- ❌ **Logic in View body:** Business logic inside SwiftUI views
  - ✅ Use: ViewModel methods
- ❌ **Direct service instantiation:** `let service = MyService()` in ViewModel
  - ✅ Use: Protocol injection via `init(service: ServiceProtocol)`
- ❌ **Stateful service classes:** Services as classes with stored properties
  - ✅ Use: `struct` services (stateless and Sendable)

### Concurrency
- ❌ **Force unwrap:** `value!` outside test code
  - ✅ Use: `guard let`, `if let`, or `??`
- ❌ **Parsing AI output:** `response.output` with `@Generable`
  - ✅ Use: `response.content` for structured data

### Common Mistakes
```swift
// ❌ WRONG
struct MyView: View {
    @State private var viewModel: MyViewModel
    
    init(viewModel: MyViewModel) {
        _viewModel = State(initialValue: viewModel)  // Creates copy!
    }
}

// ✅ CORRECT
struct MyView: View {
    let viewModel: MyViewModel  // Reference to injected instance
}
```

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
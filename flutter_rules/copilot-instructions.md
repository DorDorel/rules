# Flutter Project Rules — Riverpod, Clean Architecture & Performance

> For AI Agents: Be strict at boundaries. Pragmatic everywhere else.

---

## 1. Role & Persona

Senior Flutter Architect building high-performance mobile apps with Flutter 3.27+ and Dart 3.6+.

**Stack:**
- Flutter 3.27+ (Impeller Engine)
- Dart 3.6+ (Records, Patterns, Sealed Classes)
- Riverpod 2.5+ (Generator Mode)
- Clean Architecture (Feature-First)

---

## 2. Operating Modes (Context-Aware Strictness)

The codebase operates in **two modes**.

### A. UI Mode (Default)
Applies to:
- Regular Flutter widgets
- Screens, forms, lists, settings
- App-internal features

**Characteristics:**
- Pragmatic over dogmatic
- Optimize for readability and simplicity
- Architecture where it adds value

### B. Plugin/Package Mode
Applies when code involves:
- Public API surfaces
- Flutter plugins
- Background tasks (WorkManager, notifications)
- Packages for pub.dev

**Characteristics:**
- Strict interface definitions
- Comprehensive error handling
- Production-grade robustness
- Backward compatibility considerations

---

### Critical Meta-Rule

**If a rule is not explicitly applicable to the current mode, do not escalate strictness.**

Examples:

```dart
// UI Mode: Simple counter
@riverpod
class Counter extends _$Counter {
  @override
  int build() => 0;
  void increment() => state++;
}

class CounterView extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(counterProvider);
    return Text('$count');
  }
}

// ✅ This is fine - no repository interface needed
// ✅ No Result type needed
// ✅ No complex state modeling needed
// ❌ Don't force architecture that adds no value
```

```dart
// Plugin/Package Mode: Public API
abstract interface class IStoragePlugin {
  // ✅ Interface IS needed (public contract)
  // ✅ Result type IS needed (error handling)
  Future<Result<String, StorageException>> read(String key);
}
```

### Rule Application Decision Tree

When implementing a feature, ask:

1. **Is this a public API?** (Plugin, package, background service)
   - Yes → Plugin/Package Mode
   - No → Continue

2. **Does this involve I/O?** (Network, Database, File System)
   - Yes → Apply interface + Result type
   - No → Continue

3. **Is this shared across 3+ features?**
   - Yes → Extract to interface / shared provider
   - No → Keep simple

4. **Is state complex or async?**
   - Yes → Use AsyncNotifier with sealed state
   - No → Simple `@riverpod int build() => 0` is fine

**Rule Application:**
- Network rules apply only when making network calls
- Interface rules apply only when abstraction adds value
- Testing rules scale with criticality
- Accessibility rules always apply (safety-critical)

**Guiding Principle:**  
Architecture serves the code, not the other way around.

---

## 3. Architecture & Structure

### Feature-First Layout

```
lib/src/
├── features/[feature]/
│   ├── domain/        // entities, repository interfaces
│   ├── data/          // repositories, DTOs, data sources
│   └── presentation/  // controllers, widgets
│       ├── controllers/
│       └── widgets/
├── core/
│   ├── theme/
│   ├── router/
│   └── network/
└── main.dart
```

**Important:** This structure defines **project boundaries**, not widget composition rules.

- **Domain** contains business logic contracts (entities, interfaces)
- **Data** contains concrete implementations (repositories, DTOs)
- **Presentation** contains UI and controllers

**Widget Composition (within Presentation files):**
- Breaking a widget into sub-widgets is encouraged for readability
- Sub-widgets can live in the same file as parent widget
- Don't create a file per sub-widget unless it's reused across features
- Don't create a `components/` folder for every small widget

```dart
// ✅ GOOD: All in one file (features/auth/presentation/widgets/login_view.dart)
class LoginView extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        _LoginHeader(),
        _LoginForm(),
        _SocialButtons(),
      ],
    );
  }
}

class _LoginHeader extends StatelessWidget { ... }
class _LoginForm extends ConsumerWidget { ... }
class _SocialButtons extends StatelessWidget { ... }

// ❌ OVERKILL: Don't do this
// login_view.dart
// widgets/login_header.dart
// widgets/login_form.dart
// widgets/social_buttons.dart
```

**When to extract to separate file:**
- Widget is reused across 3+ features → move to `core/widgets/`
- Widget file exceeds 500 lines → split by logical screens
- Widget has its own controller → gets its own file

### Boundaries
- Domain is pure (no Flutter imports)
- Data implements Domain contracts
- Presentation is UI-only

---

## 4. Contract-First Development (MANDATORY)

**Critical Rule:** Every feature capability involving I/O MUST start with a Domain interface definition.

### Two-Step Process

**Step 1: Interface Design (SHOW FIRST)**
- Define the repository interface in Domain layer
- Include all method signatures with return types
- Document expected behavior
- **WAIT for approval before implementing**

**Step 2: Implementation (AFTER APPROVAL)**
- Implement concrete repository in Data layer
- Inject via Riverpod provider
- Create mock for tests

### Interface Design Guidelines

A good interface:
- **Minimal surface:** Only essential methods
- **Clear semantics:** No ambiguous method names
- **Explicit errors:** Use `Result<T, E>` type for operations that can fail
- **No leaky abstractions:** No implementation details in signature
- **Future-proof:** Easy to extend without breaking changes

**Example of GOOD interface:**
```dart
abstract interface class IPaymentRepository {
  Future<Result<Transaction, PaymentException>> processPayment({
    required double amount,
    required PaymentMethod method,
  });
}

@freezed
sealed class PaymentException with _$PaymentException {
  const factory PaymentException.insufficientFunds() = InsufficientFundsException;
  const factory PaymentException.invalidCard() = InvalidCardException;
  const factory PaymentException.networkError() = NetworkErrorException;
}
```

**Example of BAD interface:**
```dart
abstract class PaymentRepository {
  // ❌ Too many methods
  Future<bool> validateCard();
  Future<String> chargeCard();
  Future<Dio> getHttpClient();  // ❌ Leaky abstraction
  Future<dynamic> process();     // ❌ Untyped return, no error modeling
}
```

### Why This Matters
1. **Human Review:** Developer reviews the contract before implementation
2. **Testability:** Interface enables easy mocking
3. **Flexibility:** Implementation can change without breaking dependents
4. **Clarity:** Forces explicit definition of capabilities

### Exceptions
- Simple state providers (counter, toggle, form state)
- Pure UI state with no I/O
- Trivial helpers with no business logic

---

## 5. Modern Dart (3.6+)

### Isolate Offloading

The Main Thread is for UI only.

**Rule:** Use `Isolate.run()` for heavy synchronous work (JSON parsing 100+ items, image processing, complex sorting).

**Critical:** Functions passed to isolates must be:
- Top-level functions
- Static class methods
- **No closures that capture context**

**Common Mistakes:**

```dart
// ❌ WRONG - Instance method cannot cross isolate boundary
await Isolate.run(() => repository.parseProducts(data));

// ❌ WRONG - Closure captures variable
final userId = currentUser.id;
await Isolate.run(() => processUser(userId)); // Closure!

// ❌ WRONG - Passing fromJson callback
await Isolate.run(() => ProductDTO.fromJson(data));

// ✅ CORRECT - Top-level or static function
static List<ProductDTO> _parseProducts(List<dynamic> jsonList) {
  return jsonList
      .map((json) => ProductDTO.fromJson(json as Map<String, dynamic>))
      .toList();
}

// Usage
final jsonList = response.data as List;
final products = await Isolate.run(() => _parseProducts(jsonList));
```

**When to use:**
- Parsing JSON arrays > 100 items
- Image decoding/processing (use `compute()` for this)
- Compute-heavy algorithms
- Large file operations

**When NOT to use:**
- Simple JSON objects (< 50 fields)
- Network calls (already async)
- Database queries (use async APIs)
- Small lists (< 50 items)

### Records & Patterns

Use **Records** for returning multiple values from internal functions.

```dart
// Good use of Records
(int statusCode, String message) _validateResponse(Response response) {
  if (response.statusCode == 200) return (200, 'Success');
  return (response.statusCode ?? 0, 'Failed');
}
```

Use **Pattern Matching** with `switch` expressions for control flow.

```dart
return switch (state) {
  AsyncData(:final value) => ContentView(value),
  AsyncLoading() => CircularProgressIndicator(),
  AsyncError(:final error) => ErrorView(error),
  _ => SizedBox.shrink(),
};
```

### Class Modifiers

- Use `sealed` for state/result types (exhaustive matching)
- Use `interface` for repository contracts (strict implementation)
- Use `final` for classes that shouldn't be extended

```dart
// State modeling
sealed class AuthState {}
final class Authenticated extends AuthState {
  final User user;
  Authenticated(this.user);
}
final class Unauthenticated extends AuthState {}

// Repository contract
abstract interface class IAuthRepository {
  Future<Result<User, AuthException>> login(String email, String password);
}
```

---

## 6. Riverpod & State Management

### Generator Mode

- **ALWAYS** use `@riverpod` annotations
- Never write manual providers
- Controllers extend `_$ControllerName`
- `build()` is strictly for initialization

### AsyncValue Pattern

Methods (actions) return `Future<void>` and mutate `state`.

```dart
@riverpod
class UserController extends _$UserController {
  @override
  FutureOr<User> build(String userId) async {
    // Initialization only
    final repo = ref.read(userRepositoryProvider);
    return repo.getUser(userId);
  }

  Future<void> updateProfile(String name) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repo = ref.read(userRepositoryProvider);
      return repo.updateUser(name);
    });
  }
}
```

### Optimistic Updates

Update local state immediately before network call.

```dart
Future<void> toggleFavorite(String itemId) async {
  final previous = state.value;
  
  // Optimistic update
  state = AsyncData(previous?.copyWith(isFavorite: !previous.isFavorite));
  
  try {
    await ref.read(itemRepositoryProvider).toggleFavorite(itemId);
  } catch (e) {
    // Revert on failure
    state = AsyncData(previous);
    rethrow;
  }
}
```

### Side Effects

**NEVER** trigger navigation or show SnackBars inside `build()`.

Use `ref.listen` in widget's `build()` to react to state changes.

```dart
class ItemView extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen(itemControllerProvider, (previous, next) {
      if (next is AsyncError) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(next.error.toString())),
        );
      }
    });

    final state = ref.watch(itemControllerProvider);
    // Build UI...
  }
}
```

### AutoDispose

- `@riverpod` is auto-dispose by default
- Use `keepAlive()` in `build()` for persistent state

```dart
@riverpod
class AppConfig extends _$AppConfig {
  @override
  FutureOr<Config> build() async {
    ref.keepAlive(); // Survives navigation
    return fetchConfig();
  }
}
```

---

## 7. SwiftUI View Rules

- `build()` must be small and pure
- No business logic in widgets
- Extract complex sub-widgets early
- Prefer composition over conditionals

### Lists & Performance

Always use stable identity:

```dart
// Good
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    final item = items[index];
    return ItemTile(
      key: ValueKey(item.id), // Stable identity
      item: item,
    );
  },
)
```

### Const Correctness

Apply `const` aggressively for widget caching:

```dart
// Good
const Padding(
  padding: EdgeInsets.all(16),
  child: Text('Hello'),
)

// Bad - Creates new instances on every rebuild
Padding(
  padding: EdgeInsets.all(16),
  child: Text('Hello'),
)
```

---

## 8. Network Layer (Conditional)

**When to use centralized ApiClient:**
- Multiple features make network calls
- Shared authentication/headers needed
- Consistent error handling across app
- Complex request/response pipeline

**When direct Dio/http is acceptable:**
- Simple background tasks (WorkManager)
- One-off requests in prototypes
- Single isolated network call with no shared config

### Centralized Pattern (Multi-Feature Apps)

Never call `Dio()` or `http.Client()` directly in feature code.

**Required:**

```dart
@riverpod
Dio dio(DioRef ref) {
  final dio = Dio(BaseOptions(
    baseUrl: 'https://api.example.com',
    connectTimeout: Duration(seconds: 10),
  ));
  
  dio.interceptors.add(AuthInterceptor(ref));
  dio.interceptors.add(LogInterceptor());
  
  return dio;
}

@riverpod
ApiClient apiClient(ApiClientRef ref) {
  return ApiClient(ref.read(dioProvider));
}

final class ApiClient {
  final Dio _dio;
  ApiClient(this._dio);

  Future<T> get<T>({
    required String path,
    required T Function(Map<String, dynamic>) fromJson,
  }) async {
    try {
      final response = await _dio.get(path);
      
      if (response.statusCode == null || 
          response.statusCode! < 200 || 
          response.statusCode! >= 300) {
        throw ServerException(statusCode: response.statusCode ?? 0);
      }

      final data = response.data as Map<String, dynamic>;
      return fromJson(data);

    } on DioException catch (e) {
      throw NetworkException.fromDio(e);
    }
  }
}
```

**Benefits:**
- Single decoder configuration
- Consistent error mapping
- Auth header injection point
- Request/response logging

### Simple Pattern (Background Tasks, Prototypes)

Direct http/Dio is acceptable when:
- No shared configuration needed
- One-off operation
- No cross-feature consistency required

```dart
@pragma('vm:entry-point')
void backgroundFetchTask() async {
  final response = await http.get(Uri.parse('https://api.example.com/ping'));
  // Process...
}
```

### Migration Trigger

**Introduce ApiClient when:**
- 3+ network call sites exist
- Need shared auth headers
- Same decoder config repeated
- Error handling duplicated

**Refactoring is straightforward:**
```dart
// Before: Scattered calls
final response = await dio.get('/users');
final user = UserDTO.fromJson(response.data);

// After: Centralized
final user = await ref.read(apiClientProvider).get(
  path: '/users',
  fromJson: UserDTO.fromJson,
);
```

### Error Normalization

```dart
@freezed
sealed class NetworkException with _$NetworkException implements Exception {
  const factory NetworkException.noInternet() = NoInternetException;
  const factory NetworkException.timeout() = TimeoutException;
  const factory NetworkException.unauthorized() = UnauthorizedException;
  const factory NetworkException.serverError(int code) = ServerException;

  factory NetworkException.fromDio(DioException error) {
    return switch (error.type) {
      DioExceptionType.connectionTimeout || 
      DioExceptionType.receiveTimeout => NetworkException.timeout(),
      DioExceptionType.connectionError => NetworkException.noInternet(),
      DioExceptionType.badResponse => switch (error.response?.statusCode) {
        401 => NetworkException.unauthorized(),
        >= 500 => NetworkException.serverError(error.response!.statusCode!),
        _ => NetworkException.unknown('HTTP ${error.response?.statusCode}'),
      },
      _ => NetworkException.unknown(error.message ?? 'Unknown error'),
    };
  }
}
```

---

## 9. Service Layer & Data Safety

### Repository Pattern

- **Domain:** Define `abstract interface class IRepository`
- **Data:** Implement `final class Repository implements IRepository`

```dart
// domain/repositories/i_auth_repository.dart
abstract interface class IAuthRepository {
  Future<Result<User, AuthException>> login(String email, String password);
}

// data/repositories/auth_repository.dart
final class AuthRepository implements IAuthRepository {
  final ApiClient _client;
  
  AuthRepository(this._client);

  @override
  Future<Result<User, AuthException>> login(String email, String password) async {
    try {
      final dto = await _client.post(
        path: '/auth/login',
        body: {'email': email, 'password': password},
        fromJson: UserDTO.fromJson,
      );
      return Result.success(dto.toDomain());
    } on NetworkException catch (e) {
      return Result.failure(AuthException.fromNetwork(e));
    }
  }
}
```

### DTOs vs Entities

**Strict Separation:** UI must NEVER see raw API JSON or Firestore snapshots.

```dart
// data/dtos/user_dto.dart
@freezed
class UserDTO with _$UserDTO {
  const factory UserDTO({
    required String id,
    required String email,
    @JsonKey(name: 'display_name') String? displayName,
  }) = _UserDTO;

  factory UserDTO.fromJson(Map<String, dynamic> json) => 
    _$UserDTOFromJson(json);
}

extension UserDTOX on UserDTO {
  UserEntity toDomain() => UserEntity(
    id: UserId(id),
    email: Email(email),
    displayName: displayName ?? 'Unknown',
  );
}
```

### Result Type Pattern

```dart
@freezed
sealed class Result<T, E> with _$Result<T, E> {
  const factory Result.success(T data) = Success<T, E>;
  const factory Result.failure(E error) = Failure<T, E>;
}
```

---

## 10. Firebase Integration

### Isolation

Firebase packages are forbidden in `domain` and `presentation`. They exist only in `data`.

### Type Safety

Use `.withConverter<T>()` for Firestore references:

```dart
final usersRef = FirebaseFirestore.instance
  .collection('users')
  .withConverter<UserDTO>(
    fromFirestore: (snapshot, _) => UserDTO.fromFirestore(snapshot),
    toFirestore: (dto, _) => dto.toJson(),
  );

final userDoc = await usersRef.doc(userId).get();
final user = userDoc.data(); // Returns UserDTO?, not dynamic
```

### Real-time Listeners

Wrap Firestore streams in Riverpod StreamProviders:

```dart
@riverpod
Stream<List<Message>> chatMessages(ChatMessagesRef ref, String chatId) {
  final firestore = ref.read(firestoreProvider);
  return firestore
    .collection('chats/$chatId/messages')
    .orderBy('timestamp', descending: true)
    .withConverter<MessageDTO>(
      fromFirestore: (snap, _) => MessageDTO.fromFirestore(snap),
      toFirestore: (dto, _) => dto.toJson(),
    )
    .snapshots()
    .map((snapshot) => snapshot.docs.map((doc) => doc.data().toDomain()).toList());
}
```

---

## 11. Performance & Optimization

### Profiling Strategy

- **DevTools Performance:** Profile regularly, not just before release
  - **Frame Rendering:** Target 60fps (16.67ms) or 120fps (8.33ms)
  - **Rebuild Stats:** Use Performance Overlay
  - **Shader Compilation:** Pre-compile with `--cache-sksl`

### Performance Budgets

- **Widget Build:** < 16ms per widget
- **API Response Handling:** < 50ms from data to UI
- **List Scrolling:** Maintain 60fps minimum

### Optimization Triggers

| Symptom | Threshold | Action |
|---------|-----------|--------|
| Frame drops | < 60fps | Profile, check expensive builds |
| Jank during scroll | Noticeable stutter | `RepaintBoundary`, `const` widgets |
| Slow initial render | > 500ms | Reduce widget tree, lazy-load |
| Memory growth | > 100MB during normal use | Check for leaks, dispose properly |

### Common Patterns

```dart
// Bad - Rebuilds entire list
Consumer(
  builder: (context, ref, _) {
    final items = ref.watch(itemsProvider);
    return ListView.builder(
      itemCount: items.length,
      itemBuilder: (context, index) => ItemTile(items[index]),
    );
  },
)

// Good - Scoped rebuild per item
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    return Consumer(
      builder: (context, ref, _) {
        final item = ref.watch(itemsProvider.select((items) => items[index]));
        return ItemTile(item);
      },
    );
  },
)

// Better - Separate provider per item
ListView.builder(
  itemCount: itemIds.length,
  itemBuilder: (context, index) {
    final itemId = itemIds[index];
    return Consumer(
      builder: (context, ref, _) {
        final item = ref.watch(itemProvider(itemId));
        return ItemTile(item);
      },
    );
  },
)
```

---

## 12. Accessibility (A11y)

### Semantics

Every interactive widget MUST have proper semantics:

```dart
Semantics(
  label: 'Delete item',
  hint: 'Double tap to remove this item',
  child: IconButton(
    icon: Icon(Icons.delete),
    onPressed: onDelete,
  ),
)

// Better - Use semantic properties
IconButton(
  icon: Icon(Icons.delete),
  tooltip: 'Delete item', // Provides semantic label
  onPressed: onDelete,
)
```

### Text Scaling

Never use fixed font sizes:

```dart
// Bad
Text('Hello', style: TextStyle(fontSize: 16))

// Good
Text('Hello', style: Theme.of(context).textTheme.bodyLarge)
```

### Color Contrast

- WCAG AA contrast (4.5:1 normal, 3:1 large text)
- Never rely on color alone

```dart
// Bad
Container(color: isActive ? Colors.green : Colors.red)

// Good
Row(
  children: [
    Icon(isActive ? Icons.check_circle : Icons.error),
    Text(isActive ? 'Active' : 'Inactive'),
  ],
)
```

### Reduce Motion

```dart
final mediaQuery = MediaQuery.of(context);
final disableAnimations = mediaQuery.disableAnimations;

AnimatedContainer(
  duration: disableAnimations ? Duration.zero : Duration(milliseconds: 300),
  // ...
)
```

---

## 13. Testing Standards

### Robot Pattern (Widget Tests)

Create PageObject classes for each screen:

```dart
class LoginRobot {
  final WidgetTester tester;
  LoginRobot(this.tester);

  Future<void> enterEmail(String email) async {
    await tester.enterText(find.byKey(Key('email_field')), email);
  }

  Future<void> tapLoginButton() async {
    await tester.tap(find.byKey(Key('login_button')));
    await tester.pumpAndSettle();
  }

  void expectErrorMessage(String message) {
    expect(find.text(message), findsOneWidget);
  }
}

// Usage
testWidgets('Login shows error on invalid credentials', (tester) async {
  final robot = LoginRobot(tester);
  
  await tester.pumpWidget(ProviderScope(
    overrides: [
      authRepositoryProvider.overrideWithValue(MockAuthRepository()),
    ],
    child: MaterialApp(home: LoginView()),
  ));

  await robot.enterEmail('invalid@test.com');
  await robot.tapLoginButton();
  robot.expectErrorMessage('Invalid credentials');
});
```

### Unit Tests for Controllers

Test state transitions:

```dart
test('successful login updates state to AsyncData', () async {
  final mockRepo = MockUserRepository();
  when(() => mockRepo.login(any(), any()))
    .thenAnswer((_) async => Result.success(User(id: '1')));

  final container = ProviderContainer(
    overrides: [
      userRepositoryProvider.overrideWithValue(mockRepo),
    ],
  );

  final controller = container.read(loginControllerProvider.notifier);
  await controller.login('test@test.com', 'password');

  final state = container.read(loginControllerProvider);
  expect(state, isA<AsyncData>());
  expect(state.value?.id, '1');
});
```

---

## 14. Anti-Patterns (FORBIDDEN)

These patterns are **strictly forbidden**:

### State Management
- ❌ **Logic in UI:** `onTap: () async { await firestore... }` 
  - ✅ Use: Controller methods
- ❌ **Caching providers in local variables:** `late final controller = ref.read(...)`
  - ✅ Use: `ref.watch()` in build method
- ❌ **BuildContext across async gaps:** Using `context` after `await` without checking `mounted`
  - ✅ Use: Check `context.mounted` before navigation/SnackBars

### Architecture
- ❌ **Direct Firebase in UI:** Importing `cloud_firestore` in presentation layer
  - ✅ Use: Repository abstraction in data layer
- ❌ **Manual providers:** Writing providers without `@riverpod`
  - ✅ Use: Generator mode only
- ❌ **GetX / Global state:** Using `Get.find()` or singletons
  - ✅ Use: Riverpod dependency injection

### Performance
- ❌ **Unoptimized lists:** Using `ListView` without `.builder` for > 20 items
  - ✅ Use: `ListView.builder` with keys
- ❌ **Missing const:** Widget constructors without `const`
  - ✅ Use: `const` everywhere possible

### Concurrency
- ❌ **Unawaited futures:** Fire-and-forget async calls
  - ✅ Use: `await` or `unawaited()` with comment
- ❌ **Closures in isolates:** Passing callbacks to `Isolate.run()`
  - ✅ Use: Static/top-level functions only

### Common Mistakes

```dart
// ❌ WRONG - Caching provider reference
class MyWidget extends ConsumerStatefulWidget {
  @override
  ConsumerState<MyWidget> createState() => _MyWidgetState();
}

class _MyWidgetState extends ConsumerState<MyWidget> {
  late final controller = ref.read(myControllerProvider); // Won't rebuild!
}

// ✅ CORRECT
class MyWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final controller = ref.watch(myControllerProvider);
    return Text(controller.value);
  }
}
```

---

## 15. Agent Conduct (Meta Rules)

**Do NOT:**
- Apply formatting beyond standard `dart format`
- Reorder widget properties
- Enforce architectures beyond this doc

**Communication:**
- "consider" / "suggest" for optimizations
- "must" / "never" only for correctness

**When uncertain:** Exclude guidance.

---

### Contract-First Workflow (STRICT)

When implementing a new feature:

1. **ALWAYS present the interface definition FIRST**
2. Say: "Here's the proposed repository interface. Should I proceed with implementation?"
3. **WAIT** for human approval
4. Only then implement the concrete repository
5. Show controller integration last

**Never skip the interface review step.**

---

## Philosophy

- Contracts over concreteness
- Boundaries over convenience
- Interfaces over implementations
- Pragmatism over dogma

**Strict where it matters. Flexible where it doesn't.**
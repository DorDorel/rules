# NestJS Best Practices — DDD, Clean Architecture & Performance

> For AI Agents: Be strict at boundaries. Pragmatic everywhere else.

---

## 1. Role & Persona

Senior Backend Architect specializing in NestJS and TypeScript. Build scalable, maintainable server-side applications following Domain-Driven Design, Clean Architecture, and SOLID principles.

**Stack:**
- NestJS 10.x+ | TypeScript 5.x+ (Strict Mode)
- Domain-Driven Design with Layered Architecture
- Prisma 5.x+ or TypeORM 0.3.x+
- Passport.js (JWT/OAuth2)
- Redis (Caching) | Bull (Queues)

---

## 2. Operating Modes (Context-Aware Strictness)

The codebase operates in **two modes**.

### A. Internal Mode (Default)
Applies to:
- Internal microservices
- Admin endpoints
- Simple CRUD operations
- Development/staging environments

**Characteristics:**
- Pragmatic over dogmatic
- Simpler validation when appropriate
- Repository pattern when beneficial, not mandatory
- Direct Prisma in services acceptable for simple queries

### B. Public API Mode (Strict)
Applies when code involves:
- Public REST APIs
- Client-facing endpoints
- Third-party integrations
- Production-grade external services

**Characteristics:**
- Strict validation (class-validator)
- Comprehensive error handling
- Rate limiting
- OpenAPI documentation mandatory
- Repository pattern with interfaces

---

### Critical Meta-Rule

**If a rule is not explicitly applicable to the current mode, do not escalate strictness.**

Examples:

```typescript
// Internal Mode: Simple health check
@Controller('health')
export class HealthController {
  @Get()
  healthCheck() {
    return { status: 'ok', timestamp: Date.now() };
  }
}

// ✅ This is fine - no DTO, no service, no repository needed
// ✅ No validation needed
// ❌ Don't force architecture that adds no value
```

```typescript
// Public API Mode: User registration
@Controller('auth')
export class AuthController {
  constructor(private authService: AuthService) {}

  @Post('register')
  async register(@Body() dto: RegisterDto): Promise<AuthResponse> {
    // ✅ Full validation required
    // ✅ Service layer required
    // ✅ Proper error handling required
    return this.authService.register(dto);
  }
}
```

### Decision Tree

When implementing an endpoint, ask:

1. **Is this a public API?** (External consumers, third-party clients)
   - Yes → Public API Mode
   - No → Continue

2. **Does this handle sensitive data?** (PII, payments, authentication)
   - Yes → Apply strict validation + sanitization
   - No → Continue

3. **Is business logic shared across 3+ modules?**
   - Yes → Extract to shared service with interface
   - No → Keep in module

4. **Is domain logic complex?** (State transitions, invariants, calculations)
   - Yes → Use domain entities + repository pattern
   - No → Direct Prisma in service is acceptable

**Rule Application:**
- Validation rules apply when handling user input
- Repository interfaces apply when domain logic is complex
- Testing requirements scale with criticality
- Security rules always apply (authentication, authorization)

**Guiding Principle:**  
Architecture serves the business logic, not the other way around.

---

## 3. Architecture & Structure

### Domain-Driven Design Layout

```
src/
├── modules/
│   ├── users/
│   │   ├── application/        # Use cases, DTOs, services
│   │   ├── domain/             # Entities, value objects, exceptions
│   │   ├── infrastructure/     # Repositories, external services
│   │   ├── presentation/       # Controllers, guards
│   │   └── users.module.ts
│   ├── orders/
│   │   └── ... (same structure)
├── common/
│   ├── decorators/
│   ├── filters/
│   ├── guards/
│   ├── interceptors/
│   └── pipes/
├── config/
├── database/
└── main.ts
```

**Important:** This structure defines **project boundaries**, not file granularity.

**File Organization (within modules):**
- Multiple related DTOs can live in same file
- Small entities/value objects can be co-located
- Don't create a file per exception unless it has complex logic
- Don't create a file per small utility function

```typescript
// ✅ GOOD: Related DTOs in one file
// modules/users/application/dtos/user.dto.ts
export class CreateUserDto { ... }
export class UpdateUserDto { ... }
export class UserResponseDto { ... }

// ✅ GOOD: Related exceptions
// modules/users/domain/exceptions/user.exceptions.ts
export class UserNotFoundException extends DomainException { ... }
export class UserAlreadyExistsException extends DomainException { ... }
export class InvalidPasswordException extends DomainException { ... }

// ❌ OVERKILL: Don't do this
// dtos/create-user.dto.ts
// dtos/update-user.dto.ts
// dtos/user-response.dto.ts
// exceptions/user-not-found.exception.ts
// exceptions/user-already-exists.exception.ts
```

**When to extract to separate file:**
- DTO/Exception used across 3+ modules → Move to `common/`
- File exceeds 300 lines → Split by logical groups
- Entity has complex behavior → Separate file with tests

### Layer Boundaries
- **Domain:** Pure TypeScript (no NestJS, no Prisma)
- **Application:** Business logic, orchestration
- **Infrastructure:** External dependencies (Prisma, APIs, Redis)
- **Presentation:** HTTP concerns only (controllers, guards, pipes)

---

## 4. Contract-First Development (MANDATORY for Public APIs)

**Critical Rule:** Public-facing features MUST start with interface definition.

### Two-Step Process

**Step 1: Interface Design (SHOW FIRST)**
- Define service/repository interface in domain layer
- Include all method signatures with return types
- Document domain exceptions
- **WAIT for approval before implementing**

**Step 2: Implementation (AFTER APPROVAL)**
- Implement concrete service/repository
- Inject via NestJS DI
- Create mock for tests

### Interface Design Guidelines

A good interface:
- **Minimal surface:** Only essential methods
- **Clear semantics:** No ambiguous method names
- **Explicit errors:** Domain exceptions defined
- **No leaky abstractions:** No Prisma types in signatures
- **Future-proof:** Easy to extend without breaking changes

**Example of GOOD interface:**

```typescript
// STEP 1: Show this first and wait

// domain/repositories/i-user.repository.ts
export interface IUserRepository {
  findById(id: string): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
  create(data: CreateUserData): Promise<User>;
  update(id: string, data: Partial<User>): Promise<User>;
}

// domain/exceptions/user.exceptions.ts
export class UserNotFoundException extends DomainException {
  constructor(userId: string) {
    super(`User ${userId} not found`, 'USER_NOT_FOUND');
  }
}

export class UserAlreadyExistsException extends DomainException {
  constructor(email: string) {
    super(`User with email ${email} already exists`, 'USER_ALREADY_EXISTS');
  }
}

// STEP 2: Only after approval

// infrastructure/user.repository.ts
@Injectable()
export class UserRepository implements IUserRepository {
  constructor(private prisma: PrismaService) {}

  async findById(id: string): Promise<User | null> {
    const data = await this.prisma.user.findUnique({ where: { id } });
    return data ? this.toDomain(data) : null;
  }

  // ... other methods
}
```

**Example of BAD interface:**

```typescript
// ❌ Leaky abstraction
export interface IUserRepository {
  findById(id: string): Promise<PrismaUser>; // ❌ Prisma type leaked
  getRawConnection(): PrismaClient; // ❌ Infrastructure leak
}

// ❌ Too many methods
export interface IUserService {
  createUser(...): Promise<User>;
  updateUser(...): Promise<User>;
  deleteUser(...): Promise<void>;
  validateEmail(...): boolean; // ❌ Should be in domain entity
  hashPassword(...): string; // ❌ Should be utility
  sendWelcomeEmail(...): void; // ❌ Should be separate service
}
```

### Why This Matters
1. **Human Review:** Developer reviews the contract before implementation
2. **Testability:** Interface enables easy mocking
3. **Flexibility:** Implementation can change (Prisma → TypeORM) without breaking code
4. **Clarity:** Forces explicit definition of capabilities

### Exceptions
- Simple CRUD endpoints with no business logic
- Internal admin endpoints
- Utility services with no external dependencies
- Prototypes/POCs

---

## 5. TypeScript Excellence

### Strict Mode (Non-Negotiable)

```json
{
  "compilerOptions": {
    "strict": true,
    "strictNullChecks": true,
    "noImplicitAny": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true
  }
}
```

### Utility Types for Domain Logic

```typescript
// Good
type CreateUserInput = Omit<User, 'id' | 'createdAt' | 'updatedAt'>;
type UpdateUserInput = Partial<CreateUserInput>;

// Better - Explicit types for business operations
interface CreateUserCommand {
  readonly email: string;
  readonly name: string;
  readonly password: string;
}

interface UserDTO {
  readonly id: string;
  readonly email: string;
  readonly name: string;
  readonly createdAt: Date;
}
```

### Branded Types - When to Use

**Use branded types when:**
- Primitives could be confused (UserId vs ProductId vs string)
- Type carries business meaning (Email vs Username)
- Validation is critical (ensures factory function was called)

**Don't use for:**
- Simple DTOs (adds unnecessary boilerplate)
- Internal-only functions
- Types that don't risk confusion

**Pattern:**

```typescript
type UserId = string & { readonly brand: unique symbol };
type Email = string & { readonly brand: unique symbol };

function createUserId(value: string): UserId {
  if (!value || value.length < 10) {
    throw new Error('Invalid user ID');
  }
  return value as UserId;
}

function createEmail(value: string): Email {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    throw new Error('Invalid email');
  }
  return value as Email;
}

// ✅ GOOD: Prevents mixing IDs
class OrderService {
  async create(userId: UserId, productId: ProductId) {
    // Cannot accidentally swap parameters at compile time
  }
}

// ❌ OVERKILL: Simple DTO
class CreatePostDto {
  title: PostTitle; // Just use string
  content: PostContent; // Just use string
}
```

---

## 6. Dependency Injection & Modules

### Provider Scope Strategy

```typescript
// Default: SINGLETON - Shared across entire application
@Injectable()
export class ConfigService {
  // Stateless, shared configuration
}

// REQUEST scope - New instance per HTTP request
@Injectable({ scope: Scope.REQUEST })
export class RequestContextService {
  constructor(@Inject(REQUEST) private request: Request) {}
}

// TRANSIENT - New instance every time injected (use sparingly)
@Injectable({ scope: Scope.TRANSIENT })
export class LoggerService {}
```

### Dynamic Modules - When to Use

**Create dynamic modules when:**
- Module needs configuration (API keys, timeouts, URLs)
- Creating reusable library/package
- Same module used with different configs in different contexts

**Don't create dynamic modules for:**
- Simple feature modules
- Modules that never change config
- Internal modules used once

**Pattern:**

```typescript
// ✅ GOOD: Reusable module with configuration
@Module({})
export class EmailModule {
  static forRoot(options: EmailOptions): DynamicModule {
    return {
      module: EmailModule,
      providers: [
        { provide: 'EMAIL_OPTIONS', useValue: options },
        EmailService,
      ],
      exports: [EmailService],
      global: options.isGlobal ?? false,
    };
  }
}

// Usage
@Module({
  imports: [
    EmailModule.forRoot({
      apiKey: process.env.EMAIL_API_KEY,
      from: 'noreply@example.com',
      isGlobal: true,
    }),
  ],
})
export class AppModule {}

// ❌ OVERKILL: Feature module
@Module({})
export class UsersModule {
  static forRoot(): DynamicModule { // Why dynamic?
    return {
      module: UsersModule,
      // ... just use @Module() decorator directly
    };
  }
}
```

---

## 7. Request/Response Pipeline

### Execution Order (Critical)

```
Incoming Request
    ↓
1. Middleware (Global → Module → Route)
    ↓
2. Guards (Global → Controller → Route)
    ↓
3. Interceptors (BEFORE - Global → Controller → Route)
    ↓
4. Pipes (Global → Controller → Route → Param)
    ↓
5. Controller Method Execution
    ↓
6. Interceptors (AFTER - Route → Controller → Global)
    ↓
7. Exception Filters (Route → Controller → Global)
    ↓
Response Sent
```

### Global Pipeline Configuration

```typescript
// main.ts - Order matters
async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.setGlobalPrefix('api/v1');

  app.enableCors({
    origin: process.env.ALLOWED_ORIGINS?.split(','),
    credentials: true,
  });

  // Global middleware
  app.use(helmet());
  app.use(compression());

  // Global pipes (validation first)
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: {
        enableImplicitConversion: true,
      },
    }),
  );

  // Global interceptors
  app.useGlobalInterceptors(new LoggingInterceptor());

  // Global filters (error handling last)
  app.useGlobalFilters(new HttpExceptionFilter());

  await app.listen(3000);
}
```

---

## 8. DTOs & Validation

### Class-Validator Best Practices

```typescript
import { 
  IsEmail, 
  IsString, 
  MinLength, 
  Matches,
  IsOptional,
  ValidateNested,
  Type,
} from 'class-validator';
import { Transform } from 'class-transformer';

export class CreateUserDto {
  @IsEmail({}, { message: 'Invalid email format' })
  @Transform(({ value }) => value.toLowerCase().trim())
  readonly email: string;

  @IsString()
  @MinLength(8, { message: 'Password must be at least 8 characters' })
  @Matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, {
    message: 'Password must contain uppercase, lowercase, and number',
  })
  readonly password: string;

  @IsString()
  @MinLength(2)
  @Transform(({ value }) => value.trim())
  readonly name: string;

  @ValidateNested()
  @Type(() => AddressDto)
  @IsOptional()
  readonly address?: AddressDto;
}
```

### Custom Validators - When to Use

**Use custom validators when:**
- Validation requires database lookup
- Complex business rule spanning multiple fields
- Reusable across 3+ DTOs

**Don't use custom validators when:**
- Simple regex/length checks (use built-in decorators)
- Validation is endpoint-specific (do it in service)
- Involves slow external API calls (do it asynchronously in service)

**Pattern:**

```typescript
// ✅ GOOD: Database uniqueness check
@ValidatorConstraint({ name: 'IsUniqueEmail', async: true })
@Injectable()
export class IsUniqueEmailConstraint implements ValidatorConstraintInterface {
  constructor(private userRepository: UserRepository) {}

  async validate(email: string): Promise<boolean> {
    const user = await this.userRepository.findByEmail(email);
    return !user;
  }

  defaultMessage(): string {
    return 'Email already exists';
  }
}

export function IsUniqueEmail(validationOptions?: ValidationOptions) {
  return function (object: object, propertyName: string) {
    registerDecorator({
      target: object.constructor,
      propertyName,
      options: validationOptions,
      constraints: [],
      validator: IsUniqueEmailConstraint,
    });
  };
}

// ❌ BAD: Sync validation that could be built-in
@ValidatorConstraint()
export class IsValidEmailConstraint {
  validate(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email); // Just use @IsEmail()
  }
}

// ❌ BAD: Slow external call in validator
@ValidatorConstraint({ async: true })
export class IsValidCreditCardConstraint {
  async validate(card: string): Promise<boolean> {
    return this.stripeApi.validateCard(card); // Too slow, do in service
  }
}
```

---

## 9. Exception Handling & Error Responses

### Standardized Error Format

```typescript
import { 
  ExceptionFilter, 
  Catch, 
  ArgumentsHost, 
  HttpException, 
  HttpStatus,
  Logger,
} from '@nestjs/common';

interface ErrorResponse {
  statusCode: number;
  timestamp: string;
  path: string;
  method: string;
  message: string | string[];
  error?: string;
  stackTrace?: string;
}

@Catch()
export class HttpExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(HttpExceptionFilter.name);

  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse();
    const request = ctx.getRequest();

    const status = 
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    const message = 
      exception instanceof HttpException
        ? exception.getResponse()
        : 'Internal server error';

    const errorResponse: ErrorResponse = {
      statusCode: status,
      timestamp: new Date().toISOString(),
      path: request.url,
      method: request.method,
      message: typeof message === 'string' ? message : (message as any).message,
    };

    if (process.env.NODE_ENV === 'development') {
      errorResponse.stackTrace = (exception as Error).stack;
    }

    this.logger.error(
      `${request.method} ${request.url}`,
      (exception as Error).stack,
    );

    response.status(status).json(errorResponse);
  }
}
```

### Domain-Specific Exceptions

```typescript
export class DomainException extends Error {
  constructor(
    message: string,
    public readonly code: string,
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

export class UserNotFoundException extends DomainException {
  constructor(userId: string) {
    super(`User with ID ${userId} not found`, 'USER_NOT_FOUND');
  }
}

export class InsufficientBalanceException extends DomainException {
  constructor(required: number, available: number) {
    super(
      `Insufficient balance. Required: ${required}, Available: ${available}`,
      'INSUFFICIENT_BALANCE',
    );
  }
}
```

---

## 10. Database Layer

### ORM Selection Guidelines

**Use Prisma when:**
- Building new projects
- Type safety is priority #1
- Simple to medium complexity queries
- Strong migration tooling needed

**Use TypeORM when:**
- Existing project already uses it
- Need Active Record pattern
- Complex joins and raw SQL queries are common
- MongoDB support needed

**Never mix both in the same project** (except during migration).

### Repository Pattern

```typescript
// domain/repositories/i-user.repository.ts
export interface IUserRepository {
  findById(id: string): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
  create(data: CreateUserData): Promise<User>;
}

// infrastructure/user.repository.ts
@Injectable()
export class UserRepository implements IUserRepository {
  constructor(private prisma: PrismaService) {}

  async findById(id: string): Promise<User | null> {
    return this.prisma.user.findUnique({
      where: { id },
      include: {
        profile: true,
      },
    });
  }

  async findByEmail(email: string): Promise<User | null> {
    return this.prisma.user.findUnique({
      where: { email },
    });
  }

  async create(data: CreateUserData): Promise<User> {
    return this.prisma.user.create({
      data,
      include: { profile: true },
    });
  }
}
```

### Prevent N+1 Queries

```typescript
// Bad - N+1 query problem
async getUsersWithOrders(): Promise<UserWithOrders[]> {
  const users = await this.prisma.user.findMany();
  
  return Promise.all(
    users.map(async (user) => ({
      ...user,
      orders: await this.prisma.order.findMany({
        where: { userId: user.id },
      }),
    })),
  );
}

// Good - Single query with include
async getUsersWithOrders(): Promise<UserWithOrders[]> {
  return this.prisma.user.findMany({
    include: {
      orders: {
        orderBy: { createdAt: 'desc' },
        take: 10,
      },
    },
  });
}

// Better - Select only needed fields
async getUsersWithOrders(): Promise<UserWithOrdersDTO[]> {
  return this.prisma.user.findMany({
    select: {
      id: true,
      name: true,
      email: true,
      orders: {
        select: {
          id: true,
          total: true,
          status: true,
        },
        take: 10,
      },
    },
  });
}
```

---

## 11. Performance Optimization

### Optimization Decision Tree

**Don't optimize prematurely.** Apply these patterns only when:

**1. DataLoader / Request Batching:**
- Endpoint returns nested data (N+1 risk detected)
- Response time > 500ms
- Load testing shows query bottleneck

**2. Caching:**
- Data changes infrequently (< once per hour)
- Same data requested 10+ times per minute
- Computation is expensive (> 100ms)

**3. Raw SQL instead of ORM:**
- ORM-generated query is inefficient (verified with EXPLAIN)
- Complex aggregations with millions of rows
- Reports requiring custom optimizations

### Optimization Phases

```typescript
// Phase 1: Simple implementation (start here)
@Injectable()
export class UserService {
  async getUser(id: string): Promise<User> {
    return this.userRepository.findById(id);
  }
}

// Phase 2: Add caching ONLY if performance metrics show need
@Injectable()
export class UserService {
  @Cacheable('user:id', 3600)
  async getUser(id: string): Promise<User> {
    return this.userRepository.findById(id);
  }
}

// Phase 3: Add DataLoader ONLY if N+1 detected in production
@Injectable({ scope: Scope.REQUEST })
export class UserService {
  constructor(private userLoader: UserLoader) {}

  async getUsers(ids: string[]): Promise<User[]> {
    return this.userLoader.loadMany(ids);
  }
}
```

### Database Query Optimization

```typescript
// Bad - Loading entire objects when only IDs needed
async getUserFavoriteProductIds(userId: string): Promise<string[]> {
  const user = await this.prisma.user.findUnique({
    where: { id: userId },
    include: {
      favoriteProducts: true, // Loads all product data
    },
  });
  
  return user.favoriteProducts.map(p => p.id);
}

// Good - Select only needed fields
async getUserFavoriteProductIds(userId: string): Promise<string[]> {
  const user = await this.prisma.user.findUnique({
    where: { id: userId },
    select: {
      favoriteProducts: {
        select: { id: true },
      },
    },
  });
  
  return user.favoriteProducts.map(p => p.id);
}
```

---

## 12. Testing Standards

### Testing Priorities

**Must test (blocker for merge):**
- [ ] Services with business logic (unit tests)
- [ ] Critical user flows (E2E tests)
- [ ] Authentication/authorization (E2E tests)
- [ ] Error scenarios (unit tests)

**Should test (nice to have):**
- [ ] Repositories (integration tests)
- [ ] Custom validators
- [ ] Guards and interceptors

**Don't test:**
- Simple DTOs with only decorators
- NestJS framework code
- Third-party libraries

### Unit Tests for Services

```typescript
describe('UsersService', () => {
  let service: UsersService;
  let repository: jest.Mocked<UserRepository>;

  beforeEach(async () => {
    const mockRepository = {
      findById: jest.fn(),
      create: jest.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UsersService,
        {
          provide: UserRepository,
          useValue: mockRepository,
        },
      ],
    }).compile();

    service = module.get<UsersService>(UsersService);
    repository = module.get(UserRepository);
  });

  // ✅ Must test
  it('should return user when found', async () => {
    const mockUser = { id: '1', email: 'test@test.com' };
    repository.findById.mockResolvedValue(mockUser);

    const result = await service.findById('1');

    expect(result).toEqual(mockUser);
  });

  // ✅ Must test
  it('should throw NotFoundException when user not found', async () => {
    repository.findById.mockResolvedValue(null);

    await expect(service.findById('999')).rejects.toThrow(
      UserNotFoundException,
    );
  });
});
```

### E2E Tests

```typescript
describe('UsersController (e2e)', () => {
  let app: INestApplication;
  let authToken: string;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ whitelist: true }));
    
    await app.init();

    // Get auth token
    const response = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email: 'test@test.com', password: 'password123' });

    authToken = response.body.accessToken;
  });

  afterAll(async () => {
    await app.close();
  });

  // ✅ Must test critical flows
  it('should create new user', () => {
    return request(app.getHttpServer())
      .post('/users')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        email: 'new@test.com',
        name: 'New User',
        password: 'password123',
      })
      .expect(201)
      .expect((res) => {
        expect(res.body).toHaveProperty('id');
        expect(res.body).not.toHaveProperty('password');
      });
  });

  // ✅ Must test validation
  it('should return 400 for invalid email', () => {
    return request(app.getHttpServer())
      .post('/users')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        email: 'invalid-email',
        name: 'Test',
        password: 'password123',
      })
      .expect(400);
  });
});
```

---

## 13. Anti-Patterns (FORBIDDEN)

### Layering Violations

❌ **WRONG - Controller knows about Prisma:**
```typescript
@Controller('users')
export class UsersController {
  constructor(private prisma: PrismaService) {} // ❌ Infrastructure leak
  
  @Get(':id')
  async getUser(@Param('id') id: string) {
    return this.prisma.user.findUnique({ where: { id } }); // ❌ Direct DB
  }
}
```

✅ **CORRECT - Proper layering:**
```typescript
@Controller('users')
export class UsersController {
  constructor(private usersService: UsersService) {} // ✅ Service layer
  
  @Get(':id')
  async getUser(@Param('id') id: string) {
    return this.usersService.findById(id);
  }
}

@Injectable()
export class UsersService {
  constructor(private userRepository: IUserRepository) {} // ✅ Interface
  
  async findById(id: string): Promise<UserDTO> {
    const user = await this.userRepository.findById(id);
    if (!user) throw new UserNotFoundException(id);
    return this.toDTO(user);
  }
}
```

### Other Anti-Patterns

- ❌ **Business Logic in Controllers:** Controllers handle HTTP only, move logic to services
- ❌ **Circular Dependencies:** Avoid modules importing each other
- ❌ **Synchronous Operations in Handlers:** Never block event loop, use Bull queues
- ❌ **Missing Error Handling:** Every async operation needs try-catch or filter
- ❌ **Hardcoded Values:** Never hardcode URLs/credentials, use ConfigService
- ❌ **Global State/Singletons:** Avoid global variables, use DI
- ❌ **Unvalidated Input:** Every DTO must have validation decorators

**Rule of thumb:**
- Controllers → Services (never Repositories/Prisma)
- Services → Repositories (via interfaces for complex logic)
- Repositories → Prisma/Database

---

## 14. Agent Conduct (Meta Rules)

**Do NOT:**
- Apply formatting beyond standard Prettier/ESLint
- Reorder class methods without reason
- Enforce architectures beyond this doc

**Communication:**
- "consider" / "suggest" for optimizations
- "must" / "never" only for correctness

**When uncertain:** Exclude guidance.

---

### Contract-First Workflow (STRICT for Public APIs)

When implementing a new public-facing feature:

1. **ALWAYS present the interface definition FIRST**
2. Say: "Here's the proposed service interface and domain exceptions. Should I proceed with implementation?"
3. **WAIT** for human approval
4. Only then implement concrete service/repository
5. Show controller integration last

**For internal endpoints:** Skip interface definition unless business logic is complex.

**Never skip the interface review step for public APIs.**

---

## Philosophy

- Contracts over concreteness (at boundaries)
- Services over controllers (business logic placement)
- Interfaces over implementations (when abstraction adds value)
- Pragmatism over dogma

**Strict where it matters. Flexible where it doesn't.**
---
applyTo: "**/mobile/**/*.{swift,kt,java,dart,m,mm,tsx,jsx}"
priority: 90
category: "domain-specific"

---

# Mobile Development-specific Copilot Instructions

## iOS Development (Swift/Objective-C)

- Use Auto Layout or SwiftUI for responsive designs across all device sizes
- Implement proper memory management; avoid retain cycles with weak/unowned references
- Use Core Data or SQLite for local persistence; implement proper migration strategies
- Implement background app refresh and state restoration for seamless user experience
- Use Keychain Services for secure credential storage; never store secrets in UserDefaults
- Implement proper error handling for network requests and API calls
- Use Grand Central Dispatch (GCD) for concurrent operations; avoid blocking the main thread
- Implement accessibility features (VoiceOver, Dynamic Type, High Contrast)
- Use TestFlight for beta testing; implement crash reporting with Crashlytics or Sentry
- Follow Apple's Human Interface Guidelines for consistent user experience

## Android Development (Kotlin/Java)

- Use Jetpack Compose or XML layouts with ConstraintLayout for responsive designs
- Implement proper lifecycle management with ViewModel and LiveData/StateFlow
- Use Room for local database operations; implement proper migration strategies
- Implement background processing with WorkManager for reliable task execution
- Use Android Keystore for secure key generation and storage
- Implement proper permission handling with runtime permission requests
- Use Retrofit with coroutines for network operations; implement proper error handling
- Implement accessibility features (TalkBack, content descriptions, focus navigation)
- Use Firebase Crashlytics for crash reporting and performance monitoring
- Follow Material Design guidelines for consistent user experience

## Flutter/Dart Development

- Use BLoC or Provider pattern for state management across the application
- Implement proper widget lifecycle management; dispose controllers and streams
- Use packages like shared_preferences for simple storage, sqflite for complex data
- Implement platform-specific code using method channels when necessary
- Use flutter_secure_storage for sensitive data encryption
- Implement proper error boundaries and exception handling
- Use isolates for CPU-intensive operations to avoid blocking the UI thread
- Implement accessibility semantics for screen readers and navigation
- Use Firebase or native crash reporting for both platforms
- Test on both platforms with device-specific considerations

## Cross-Platform Considerations

- Implement platform-agnostic business logic with platform-specific UI adaptations
- Use responsive design principles for various screen sizes and orientations
- Implement offline-first architecture with proper data synchronization
- Use feature flags for gradual rollouts and A/B testing
- Implement proper app store optimization (ASO) with metadata and screenshots
- Use continuous integration for automated testing on real devices
- Implement proper app signing and certificate management
- Monitor app performance metrics (startup time, memory usage, battery consumption)
- Implement proper deep linking and universal links for seamless navigation
- Use analytics to track user behavior while respecting privacy regulations

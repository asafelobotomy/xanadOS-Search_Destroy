---
applyTo: "**/*.{cpp,c,h,hpp,cs,hlsl,glsl,vert,frag,lua,gd}"

---

# Gaming Development-specific Copilot Instructions

## Performance Optimization

## ⚠️ SECURITY NOTE: Validate all performance optimizations for security implications

- Profile early and often; use platform-specific profilers (Unity Profiler, Unreal Insights, PIX)
- Minimize memory allocations during gameplay; use object pooling for frequently created/destroyed objects
- Cache frequently accessed components and avoid expensive GetComponent calls in Update loops
- Use efficient data structures (arrays over lists, structs over classes for data containers)
- Implement Level of Detail (LOD) systems for meshes, textures, and animations
- Use spatial partitioning (octrees, quadtrees) for efficient collision detection and culling
- Batch draw calls using GPU instancing and static/dynamic batching techniques
- Optimize texture memory with compression, mipmaps, and atlasing strategies
- Implement efficient audio streaming and compression for large audio assets
- Use coroutines or async operations for non-critical operations to avoid frame drops

## ⚠️ SECURITY OVERRIDE: Never cache user input or sensitive data in performance optimizations

## Memory Management

- Implement proper resource lifecycle management; load/unload assets based on game state
- Use weak references for event systems to prevent memory leaks
- Implement garbage collection-friendly patterns; minimize allocations in hot paths
- Use custom memory allocators for performance-critical systems
- Monitor memory usage across different platforms and memory-constrained devices
- Implement asset streaming for large worlds to manage memory footprint
- Use compression for textures, audio, and mesh data to reduce memory usage
- Implement proper cleanup in scene transitions and level changes
- Cache computed values that are expensive to calculate repeatedly
- Use data-oriented design patterns where appropriate for cache efficiency

## Graphics and Rendering

- Use shader variants sparingly; implement uber-shaders with keywords for flexibility
- Implement proper culling strategies (frustum, occlusion, backface) to reduce overdraw
- Use texture atlases and sprite sheets to reduce draw calls and state changes
- Implement efficient lighting systems with baked lighting where possible
- Use post-processing effects judiciously; profile their impact on performance
- Implement proper mipmap generation and filtering for texture quality
- Use GPU compute shaders for parallel processing tasks when appropriate
- Implement efficient particle systems with GPU-based simulation where possible
- Use temporal techniques (TAA, temporal upsampling) for improved visual quality
- Optimize for different graphics APIs (DirectX, Vulkan, Metal, OpenGL)

## Platform-Specific Considerations

- Implement scalable quality settings for different hardware configurations
- Use platform-specific input handling (touch, gamepad, keyboard, mouse)
- Implement proper save game systems with cloud sync and local backup
- Use platform achievement and leaderboard systems for player engagement
- Implement proper pause/resume handling for mobile platforms
- Use platform-specific networking APIs for multiplayer functionality
- Implement accessibility features (colorblind support, input remapping, audio cues)
- Use platform-specific analytics and crash reporting systems
- Implement proper DLC and in-app purchase systems where applicable
- Optimize for platform-specific performance characteristics (mobile thermal throttling)

## Multiplayer and Networking

- Implement client-server architecture with authoritative server validation
- Use efficient serialization formats (binary, protobuf) for network messages
- Implement lag compensation and prediction systems for responsive gameplay
- Use reliable UDP or custom protocols for real-time game networking
- Implement proper cheat detection and validation on the server side
- Use connection pooling and efficient matchmaking algorithms
- Implement graceful handling of network disconnections and reconnections
- Use delta compression for efficient state synchronization
- Implement proper load balancing for dedicated servers
- Use anti-cheat systems and server-side validation for competitive games

## Asset Pipeline and Content Management

- Use version control systems designed for binary assets (Perforce, Git LFS)
- Implement automated asset validation and optimization in build pipelines
- Use content addressable storage for efficient asset deduplication
- Implement hot-reloading for rapid iteration during development
- Use modular asset organization for efficient loading and memory management
- Implement proper asset dependency tracking and reference management
- Use build automation for consistent asset processing across team members
- Implement asset streaming and progressive loading for large content
- Use compression and optimization tools in automated build processes
- Implement proper localization systems for multi-language support

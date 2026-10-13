---
name: omma-local-preview
description: Use when running or porting an exported design bundle. A bundle is a zip of front-end source with a preview host. It may run locally or move its scene into a storefront. Covers serving over HTTP, reconciling asset paths, porting to Next.js, and layering 3D content under page text.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [design-export, local-preview, vite, nextjs, three-js, assets, layout]
    category: devops
related_skills: [storefront-release-publish, cloudflare-pages-site-ship]
---

# Exported Design Bundle, Local Preview, Then Storefront

## Overview
A design tool's export is usually source code plus a preview host. The host supplies things the zip does not contain: an import map, injected global variables that point at uploaded models and images, and sometimes a runtime that loads files the export never lists. Running the export locally therefore needs three checks: that it is served over HTTP, that every asset path it asks for exists, and that any uploaded asset it expects has been located and not replaced by a guess. Porting it into a storefront then needs a set of framework changes. This skill covers both steps and the layout rules that keep 3D content from fighting the page text.

## When to Use
- An exported zip must run on a local machine for review.
- A 3D or media scene from an export must move into a production storefront.
- A preview shows a missing model, a blank scene, or a page whose layers overlap.

## Features
- A local server on a free port, never a file path.
- An asset reconciliation that compares each path in the code with the files on disk.
- A check for uploaded assets that the host injects at run time.
- Port notes for a Next.js storefront: the public folder, client-only components, and the render-target class.
- Layout rules for a sticky 3D stage, a single hero layer, and a readable text column.

## Benefits
- A missing asset is found before the reviewer sees a broken scene.
- Nothing is replaced by a file that only looks similar.
- The port keeps the current scene code, and does not copy the export as it was delivered.
- Overlapping text and 3D layers are handled by a layout rule, not by hiding content.

## Procedure
### Serve the bundle over HTTP
Never open the bundle from a file path. Start a development server from inside the unzipped folder if the package file defines one, such as `npm run dev`. Otherwise start a static server:
```zsh
python3 -m http.server <free-port>
```
Choose a port that no other project uses. A storefront often owns the common development ports.

### List what exists and what the code asks for
From inside the unzipped folder, skip the dependency folder, and compare:
```zsh
find . -path ./node_modules -prune -o -type f \( -name '*.glb' -o -name '*.gltf' \) -print
grep -rn "assets/" --include='*.js' --include='*.jsx' --include='*.html' . | grep -v node_modules
grep -rn "UPLOADED_" --include='*.js' --include='*.jsx' --include='*.html' . | grep -v node_modules
```
A loader that reads a global variable from the host does not show up as a file under `assets/`. Search for the global names as well.

### Reconcile each path
Every `assets/<name>` path in the code must exist on disk, with the same case and the same spaces. Do not rename a file to make the list tidy. If a path is wrong, fix the reference in the source, and note the change.

### Handle a model that the host should supply
If the scene expects a model and the folder has no model file, the model was probably injected by the host through a global variable. An empty search is not proof that the geometry is generated in code. Ask the operator to place the exported model file in the assets folder. Then point the loader at that path for the case where the host's global is missing.

Do not search the downloads folder for a file with a similar name. A wrong model is worse than a clearly labeled placeholder.

### Name the URL in every status
Two local servers can be running at once. State the URL the reviewer should open, every time. Stop the bundle's own preview server when the storefront serves the same scene.

### Port onto a Next.js storefront
- Copy the current scene code after the local asset path is wired. Do not copy the export as it was delivered.
- Next.js serves files from its public folder. A relative path such as `assets/<name>.glb` becomes `/<public-subfolder>/<name>.glb`. Encode spaces in the URL.
- Remove the bundle's own mount code, such as a root-render call and its entry file. The scene becomes a client component.
- Load a 3D component with dynamic import and server-side rendering turned off, from a file marked as a client component. Server components cannot disable server-side rendering for a dynamic import.
- Prefer the library's named cube render-target class, through the namespace object. A static analysis step in some build tools fails on the direct name.
- Start a development server in a background process that is not owned by the agent run that started it. When that run ends, its child processes can be stopped. Check the port with `curl` after the run ends, and do not report a server as running on the strength of the run's own note.
- For a new brand, start from the storefront starter that the platform publishes. Do not fork a live storefront that shares a backend, because the age gate, catalog text, and identity would carry over.

### Layer 3D content under page text
A 3D element that is fixed to the screen overlaps a scrolling article. Use these rules:
1. Put the 3D room in a sticky stage at full viewport height, inside a track about four viewports tall. A stage that is only one viewport tall, followed by a card, has no travel, so the scene never finishes its motion.
2. Keep one particle or motion layer on the hero. Do not stack a second animated layer on the same screen.
3. Do not repeat the same copy as an absolute overlay and as the article body.
4. Do not place a full-screen backdrop filter over text. It makes the text appear to sharpen under the cursor. Disable text selection on decorative hero text.
5. Fade the hero headline after about one viewport of scrolling. Do not fade a scrim after a few dozen pixels.
6. Keep the background photograph. Add a dark gradient behind the text column, not over the whole image, so the image stays visible behind the subject.
7. Keep only the strands of a particle system sharp. Soft large particles can form a veil. If you can count the individual circles, they are too hard.

### Put a front-depth pass in front of a transparent subject
A helix or ring that appears only behind a transparent object is usually a depth-order problem, not a radius problem:
1. Parent the particle group to the same world position as the subject.
2. After the axial spin in the vertex shader, classify the structure particles as front when their view-space distance is closer than the subject's focus distance. Classify strands and rungs, not only the dust.
3. Draw the front set after the transparent subject. Give the subject a depth-write setting, so the back set can be occluded.

## Pitfalls
- **Trusting a placeholder name.** A file name in a template is not the upload's name.
- **Concluding a model is generated because the search found none.** The host may supply it at run time.
- **Applying one material to every mesh.** A single-mesh export has no node names to filter on, so a name-based exception does nothing.
- **Two local servers and one URL.** Name the reviewer's URL each time.
- **A short hero followed by a card.** The scene has no travel. Use the sticky stage.
- **Two animated layers on one screen.** One motif on the hero.
- **Forking a live storefront for a second catalog.** Start from the starter.

## Verification
- Each asset path in the source resolves to a file on disk, with matching case and spaces.
- The review URL serves the scene, and its model loads without a console error.
- The storefront page serves the scene from its public folder, and the port answers with `curl` after the run that started it has ended.
- The layout shows one hero layer, a sticky stage with travel, and a readable text column.

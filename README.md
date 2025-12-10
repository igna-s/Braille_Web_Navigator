# Braille Web Navigator

Welcome to the **Braille Web Navigator**, an accessible web browsing engine designed to bridge the digital gap for the visually impaired. This project simulates a tactile operating system, converting live web content, search results, and even images into a readable Braille matrix.

While currently implemented as a web-based software simulation (HTML/Python), this architecture is designed to serve as the "brain" for a future physical tactile tablet device. The interface is designed to mimic a physical device with a 15x40 tactile pin matrix.

---

## 🖼️ Device Concept

<p align="center">
  <img src="Prototipe.png" alt="Device Concept" width="400"/>
</p>

## 🎥 Demo

<p align="center">
  <a href="Demo.mp4" target="_blank">
    <img src="https://img.shields.io/badge/Watch%2520Demo--2d3748?style=for-the-badge&logo=youtube" alt="Video"/>
  </a>
</p>

---

## ✨ Core Features

- **🔍 Live Web Search** Powered by DuckDuckGo and BeautifulSoup, the system scrapes the web and cleans up the UI, presenting only the essential text and navigable links.
- **📝 Text-to-Braille Engine** A custom Python backend (`traductor.PY`) translates alphanumeric characters into Spanish Braille patterns in real-time, handling special characters, numbers, and capitalization prefixes.
- **✋ Haptic Image Rendering** The system can process web images, resize them to a low-resolution grid (80x45), and convert them into binary Braille dot patterns, allowing users to "feel" images.
- **⌨️ Input Simulation** Includes a virtual Braille keyboard with three modes: Lowercase (abc), Uppercase (ABC), and Numeric (123), mimicking the input method of the physical device.
- **📄 Pagination & Navigation** Handles long web pages by splitting text into 40-character lines and managing page states (Next/Previous) automatically.

## 🛠️ Hardware Context

- **Important**: This repository represents the software stack. In the final implementation, the HTML interface (`index.html`) is intended to be replaced or mapped to a physical hardware controller (e.g., Raspberry Pi or ESP32) driving a grid of piezoelectric actuators or solenoids.
- **Green Area** (in diagrams): Represents the refreshable Braille Display (40 cells x 15 lines).
- **Orange Area**: Represents physical buttons for navigation (D-Pad) and input keys.

## 🚀 Getting Started

1. **Clone the Repository** Download the project files to your local machine.

2. **Install Dependencies** You will need Python installed on your machine. Install the following Python libraries (based on imports in `traductor.PY`):
   ```bash
   pip install flask duckduckgo-search requests beautifulsoup4 pillow
   ```

3. **Run the Server** Execute the main Python script to start the Flask backend:
   ```bash
   python traductor.PY
   ```

4. **Access the Interface** Open your web browser and navigate to the local address:
   - **URL**: `http://127.0.0.1:5000/`

   You can now type into the virtual keyboard to search the web. Try commands like simple text searches or pasting a URL.

## 📂 Project Structure

* **traductor.PY**: The core backend. Handles the Flask server, Braille translation dictionary, web scraping logic, and image processing.
* **templates/index.html**: The frontend simulation. Renders the grid visually using CSS and handles user clicks to simulate touching a physical device.
* **Translation.jpeg**: Reference chart for the Spanish Braille system used in the project.

## 🎨 Future Changes

- [ ] **Hardware Integration**: Connect the Python backend to a microcontroller via Serial/UART to drive real actuators.
- [ ] **Voice Synthesis**: Add TTS (Text-to-Speech) feedback for UI navigation.
- [ ] **Improved Image Dithering**: Optimize the algorithm for converting complex images into tactile dots.
- [ ] **Physical Case Design**: Create 3D printable STL files for the device housing.

## 📜 License

This project is open source. Feel free to modify the code to adapt it to different Braille standards or hardware configurations.

## 📜 License

This project has no usage restrictions (Uses MIT or Apache libraries), except for the terms and conditions of the respective API providers. From my side, feel free to use and evolve it :D !

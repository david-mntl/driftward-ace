# Dev container image for Driftward Ace.
# Python 3.12 matches the CPython version pygbag 0.9.x runs in the browser.

FROM python:3.12-slim

# git/curl/zsh for the dev shell. The X11 libraries let SDL open a desktop
# window through the host display (pygame-ce wheels bundle SDL itself).
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    zsh \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxcursor1 \
    libxi6 \
    libxrandr2 \
    libxfixes3 \
    libxss1 \
    libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user that matches the VS Code devcontainer convention
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME --shell /bin/zsh

# Install Oh My Zsh for a better terminal experience
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# Copy Oh My Zsh to the vscode user's home and fix ownership
RUN cp -r /root/.oh-my-zsh /home/$USERNAME/.oh-my-zsh \
    && cp /root/.zshrc /home/$USERNAME/.zshrc \
    && sed -i "s|/root|/home/$USERNAME|g" /home/$USERNAME/.zshrc \
    && chown -R $USERNAME:$USERNAME /home/$USERNAME/.oh-my-zsh /home/$USERNAME/.zshrc

# Install Python dependencies before the source is mounted so Docker can
# cache this layer. It only rebuilds when game/requirements.txt changes.
COPY game/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Browser testing for the Integration Engineer agent. CLAUDE.md requires every
# build to be tested in a real browser, so the agent drives headless Chromium
# through the Playwright MCP server (Node-based). Browsers go in a shared path
# so the non-root user can run them. Chromium's system libraries come from
# --with-deps. Run the MCP server with --headless --no-sandbox in a container.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @playwright/mcp \
    && node "$(find "$(npm root -g)" -path '*playwright/cli.js' | head -1)" install --with-deps chromium \
    && chmod -R a+rX /opt/playwright \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

USER $USERNAME

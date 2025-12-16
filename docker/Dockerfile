ARG baseImage=ubuntu:24.04
FROM ${baseImage}

# env/user defaults
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV USER=root
ENV HOME=/root
ENV LANGUAGE=C.UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TERM=xterm-256color
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NOWARNINGS=yes
ENV DEBCONF_TERSE=yes
ENV TZ=America/Los_Angeles
USER root

ARG buildDate
ENV BUILD_DATE ${buildDate}
RUN set -x && echo "${BUILD_DATE}"

# upgrade first
RUN \
  set -x && \
  apt-get update -y && \
  apt-get upgrade -y && \
  mkdir -p /etc/apt/keyrings && \
  apt-get install -y --no-install-recommends \
    apt-utils \
    apt-transport-https \
    bash-completion \
    btop \
    build-essential \
    ca-certificates \
    conntrack \
    curl \
    dirmngr \
    dialog \
    dnsutils \
    ffmpeg \
    file \
    fonts-liberation \
    fonts-powerline \
    git \
    gnupg \
    gnupg2 \
    groff \
    gzip \
    htop \
    iproute2 \
    iputils-ping \
    jq \
    less \
    libappindicator3-1 \
    libnotify-bin \
    lsb-release \
    net-tools \
    openssh-client \
    postgresql-client \
    procps \
    python-is-python3 \
    software-properties-common \
    sudo \
    tar \
    tree \
    unzip \
    vim \
    wget \
    which \
    yq

# install task
RUN \
  curl -fsSL 'https://dl.cloudsmith.io/public/task/task/setup.deb.sh' | bash && \
  apt-get install -y task

# install vault
RUN \
  wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null && \
  echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
  apt-get update && \
  apt-get install -y vault

# install specific node version
ARG nodeVersion
ENV NODE_VERSION=${nodeVersion}
RUN \
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
  echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_VERSION}.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
  apt-get update && \
  apt-get install -y nodejs && \
  node -v && \
  npm -v && \
  npm install -g npm@latest

# install uv and python
ENV UV_TOOL_BIN_DIR=/usr/local/bin
ENV PATH="${PATH}:/usr/local/bin"
RUN \
  curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR="/usr/local/bin" bash && \
  uv --version

# use uv to install python
ARG pythonVersion
ENV PYTHON_VERSION=${pythonVersion}
RUN \
  set -x && \
  cd /tmp && \
  uv python install ${PYTHON_VERSION} && \
  python --version

# create venv and install packages
ENV VIRTUAL_ENV=/opt/venv
RUN \
  set -x && \
  cd /tmp && \
  uv venv --python ${PYTHON_VERSION} ${VIRTUAL_ENV}

ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
RUN  \
  set -x && \
  cd /tmp && \
  uv pip install playwright numpy

# install cli tools (goes to ~/.local/bin)
RUN \
  set -x && \
  cd /tmp && \
  uv tool install black

# install gomplate
COPY --from=hairyhenderson/gomplate:stable /gomplate /bin/gomplate

# install docker
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update && apt-get install -y docker-ce-cli

# install nvidia-container-toolkit
RUN \
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
      tee /etc/apt/sources.list.d/nvidia-container-toolkit.list && \
  apt-get update && \
  apt-get install -y nvidia-container-toolkit && \
  nvidia-ctk runtime configure --runtime=docker

# install kubectl
ARG kubectlVersion
RUN \
  cd /tmp && \
  curl -LO "https://dl.k8s.io/release/v${kubectlVersion}/bin/linux/amd64/kubectl" && \
  install kubectl /usr/local/bin/kubectl && \
  rm kubectl

# install minikube cli
RUN \
  cd /tmp && \
  curl -LO "https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64" && \
  install minikube-linux-amd64 /usr/local/bin/minikube && \
  rm minikube-linux-amd64

# install helm
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# install powershell
ARG powershellVersion
ENV PWSH_VERSION=${powershellVersion}
RUN \
  . /etc/os-release && \
  wget -q https://github.com/PowerShell/PowerShell/releases/download/v${PWSH_VERSION}/powershell_${PWSH_VERSION}-1.deb_amd64.deb && \
  dpkg -i powershell_${PWSH_VERSION}-1.deb_amd64.deb && \
  rm powershell_${PWSH_VERSION}-1.deb_amd64.deb && \
  apt-get update && \
  apt-get install -y powershell && \
  pwsh --version

# install ansible
RUN \
  set -x && \
  add-apt-repository --yes --update ppa:ansible/ansible && \
  apt install -y ansible

# install open tofu
RUN \
  set -x && \
  cd /tmp && \
  curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh && \
  chmod +x install-opentofu.sh && \
  ./install-opentofu.sh --install-method deb && \
  rm -f install-opentofu.sh

# install full chrome (overkill)
RUN \
  cd /tmp && \
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
  apt install -y ./google-chrome-stable_current_amd64.deb

# install headless chrome
RUN \
  npx @puppeteer/browsers install chrome-headless-shell@stable --path /usr/local/share/chrome && \
  ln -s /usr/local/share/chrome/chrome-headless-shell/linux-*/chrome-headless-shell-linux64/chrome-headless-shell /usr/local/bin/chrome-headless-shell && \
  chrome-headless-shell --version

# install playwright with chromium
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright
RUN python -m playwright install chromium --with-deps
RUN chmod -R 755 ${PLAYWRIGHT_BROWSERS_PATH}


# install jdk and maven
ARG jdkVersion
ENV JDK_VERSION=${jdkVersion}
ENV JAVA_HOME=/usr/lib/jvm/java-${JDK_VERSION}-openjdk-amd64
RUN \
  apt-get update && \
  apt-get install -y \
  openjdk-${JDK_VERSION}-jdk \
  maven && \
  java -version && \
  mvn -version

# install go
ARG goVersion
ENV GOBIN=/usr/local/bin
ENV GO_VERSION=${goVersion}
ENV GO_TARBALL=go${GO_VERSION}.linux-amd64.tar.gz
ENV GO_URL=https://go.dev/dl/${GO_TARBALL}
ENV GOROOT=/usr/local/go
ENV PATH=$GOROOT/bin:$PATH
RUN \
  set -x && \
  cd /tmp && \
  curl -fsSL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz -o /tmp/go.tar.gz && \
  rm -rf ${GOROOT} && \
  tar -C /usr/local -xzf /tmp/go.tar.gz && \
  rm /tmp/go.tar.gz && \
  go version

# install rust
ARG rustVersion
ENV RUST_VERSION=${rustVersion}
ENV CARGO_HOME=/usr/local/cargo
ENV RUSTUP_HOME=/usr/local/rustup
ENV PATH=$CARGO_HOME/bin:$PATH
RUN \
  set -x && \
  cd /tmp && \
  curl https://sh.rustup.rs -sSf | sh -s -- -y --no-modify-path --default-toolchain ${RUST_VERSION} && \
  rustc --version && cargo --version

# setup aws-cli v2
RUN \
  set -x && \
  cd /tmp && \
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
  unzip -qq awscliv2.zip && \
  ./aws/install && \
  aws --version

# install SAM CLI
RUN \
  set -x && \
  cd /tmp && \
  curl -fsSL "https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip" -o "aws-sam-cli.zip" && \
  unzip aws-sam-cli.zip -d sam-installation && \
  ./sam-installation/install && \
  rm -rf aws-sam-cli.zip sam-installation

# install CDK CLI
RUN npm install -g aws-cdk

# install additional useful tools
RUN npm install -g @aws-cdk/aws-lambda-nodejs

# install gcloud
ENV CLOUDSDK_PYTHON_SITEPACKAGES=1
ENV CLOUDSDK_PYTHON=${VIRTUAL_ENV}/bin/python
RUN \
  set -x && \
  cd /tmp && \
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
  apt-get update && \
  apt-get install -y google-cloud-cli

# install gcloud sql proxy
ARG sqlProxyVersion
ENV CLOUD_SQL_PROXY_VERSION=${sqlProxyVersion}
RUN \
  set -x && \
  cd /tmp && \
  curl -fsSL https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v${CLOUD_SQL_PROXY_VERSION}/cloud-sql-proxy.linux.amd64 -o cloud-sql-proxy && \
  mv cloud-sql-proxy /usr/local/bin && \
  chmod +x /usr/local/bin/cloud-sql-proxy

# install google mcp-genmedia tools
RUN \
  set -x && \
  cd /tmp && \
  git clone --depth=1 https://github.com/GoogleCloudPlatform/vertex-ai-creative-studio.git && \
  cd vertex-ai-creative-studio/experiments/mcp-genmedia/mcp-genmedia-go && \
  cd ./mcp-chirp3-go; go install; cd ..&& \
  cd ./mcp-imagen-go; go install; cd ..&& \
  cd ./mcp-veo-go; go install; cd ..&& \
  cd ./mcp-avtool-go; go install; cd ..&& \
  cd ./mcp-lyria-go; go install

# install pulumi
RUN \
  set -x && \
  cd /tmp && \
  curl -fsSL https://get.pulumi.com | sh && \
    mv /root/.pulumi/bin/pulumi /usr/local/bin/

# aws powershell tools
RUN \
  pwsh -Command "Install-Module -Name AWSPowerShell.NetCore -Scope AllUsers -Force"

# install oh-my-posh
RUN \
  curl -s https://ohmyposh.dev/install.sh | bash -s -- -d /usr/local/bin

# download oh-my-posh theme
ARG poshThemesURL=https://raw.githubusercontent.com/JanDeDobbeleer/oh-my-posh/refs/heads/main/themes
ARG poshThemesPath=/poshthemes
ARG poshTheme=paradox
ENV POSH_THEMES_URL=${poshThemesURL}
ENV POSH_THEMES_PATH=${poshThemesPath}
ENV POSH_THEME=${poshTheme}
RUN \
  mkdir -p ${POSH_THEMES_PATH} && \
  curl -fsSL -o ${POSH_THEMES_PATH}/${POSH_THEME}.omp.json ${POSH_THEMES_URL}/${POSH_THEME}.omp.json

# install github (gh) cli
RUN \
  mkdir -p -m 755 /etc/apt/keyrings \
    && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && gh --version

# install gitlab cli
ARG glabVersion
ENV GLAB_VERSION=${glabVersion}
RUN \
  curl -fsSL "https://gitlab.com/gitlab-org/cli/-/releases/v${GLAB_VERSION}/downloads/glab_${GLAB_VERSION}_linux_amd64.deb" -o /tmp/glab.deb && \
  dpkg -i /tmp/glab.deb && \
  rm /tmp/glab.deb

# install bunx
RUN curl -fsSL https://bun.sh/install | BUN_INSTALL=/usr/local bash

# install claude-code
ARG claudeCodeDate
ENV CLAUDE_CODE_DATE=${claudeCodeDate}
RUN set -x && echo "${CLAUDE_CODE_DATE}"
RUN \
  npm install -g @anthropic-ai/claude-code

# cleanup
RUN \
  apt-get clean autoclean && \
  apt-get autoremove -y && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# use opinionated paths
RUN echo "${PATH}" > /old_path_vars
ENV PATH="/bin"
ENV PATH="${PATH}:/sbin"
ENV PATH="${PATH}:/usr/local/bin"
ENV PATH="${PATH}:/usr/local/sbin"
ENV PATH="${PATH}:/usr/sbin"
ENV PATH="${PATH}:/usr/bin"
ENV PATH="${PATH}:/root/go/bin"
ENV PATH="${PATH}:/usr/local/go/bin"
ENV PATH="${PATH}:/usr/local/cargo/bin"
ENV PATH="${PATH}:/opt/microsoft/powershell/7"
ENV PATH="${PATH}:${VIRTUAL_ENV}/bin"

# unset VIRTUAL_ENV to prevent uv warning about mismatched venv at runtime
# reset CLOUDSDK_PYTHON since ${VIRTUAL_ENV}/bin/python symlink may be stale
ENV VIRTUAL_ENV=
ENV CLOUDSDK_PYTHON=/bin/python3

# copy assets
COPY ./docker-entrypoint.sh /docker-entrypoint
COPY ./docker-entrypoint.ps1 /docker-entrypoint.ps1
COPY ./docker-compose.sh /usr/local/sbin/docker-compose
COPY ./jars /jars
COPY ./fonts /fonts

# setup assets
RUN \
    set -x && \
    chmod +x /docker-entrypoint && \
    chmod +x /usr/local/sbin/docker-compose

EXPOSE 8084
ENTRYPOINT [ "/docker-entrypoint" ]
CMD [ "claude" ]

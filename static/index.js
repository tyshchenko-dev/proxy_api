document.addEventListener("DOMContentLoaded", () => {
    async function main() {
        const PORT = 3000; // ADD YOUR APP PORT
        const SERVER_IP = "" // ADD YOU SERVER IP
        const MAIN_URL = `http://${SERVER_IP}:${PORT}/`;

        const jwt = document.querySelector('input[name="jwt"]').value

        const errorElement = document.querySelector(".error");
        const errorClose = document.querySelector(".error__close");
        const overlay = document.querySelector(".overlay");
        let startButton = document.querySelector(".button__proxy-start");
        let searchButton = document.querySelector(".button__proxy-search")
        const notification = document.querySelector(".notification");

        async function searchProxy(country = null) {
            let selectedCountry = null;
            if (!country) {
                selectedCountry = document.querySelector('.select__country').value;
            } else {
                selectedCountry = country;
            }
            const proxySelectElement = document.querySelector(".select__proxy");
            const proxyContainer = document.querySelector(".proxy__list");
            if (selectedCountry) {
                window.localStorage.setItem("selected_country", selectedCountry);
                const proxyList = await getData(MAIN_URL, `proxy/configs/${selectedCountry}`, jwt);
                if (Array.isArray(proxyList.items) && proxyList.items.length > 0) {
                    proxySelectElement.innerHTML = "";
                    for (const proxy of proxyList.items) {
                        const optionElement = document.createElement("option");
                        optionElement.value = proxy.item;
                        optionElement.innerText = proxy.item;
                        proxySelectElement.appendChild(optionElement);
                    }
                    proxyContainer.classList.remove("d-none");
                }
            }
        }

      async function start() {
          overlay.classList.remove("d-none");
          const configName = document.querySelector(".select__proxy").value;
          const folderName = document.querySelector(".select__country").value;
          const response = await startProxy(MAIN_URL, "proxy/start/", configName, folderName, jwt);
          if (response.status == 200) {
            notification.textContent = "Proxy added";
            notification.classList.remove("d-none");
            await getActiveProxies();
            setTimeout(() => {
              notification.classList.add("d-none");
            },3000);
          }
          overlay.classList.add("d-none");
        }

        async function getLocales() {
            const proxyLocales = await getData(MAIN_URL, "proxy/locales/", jwt);
            if (proxyLocales["locales"]) {
                const country = window.localStorage.getItem("selected_country")
                localesList = proxyLocales["locales"];
                const proxyContainer = document.querySelector(".select__country")
                if (Array.isArray(localesList) && localesList.length > 0) {
                    for (let locale of localesList) {
                        const optionElement = document.createElement("option");
                        optionElement.value = locale.item;
                        optionElement.innerText = locale.item;
                        if (locale.item == country) {
                            optionElement.setAttribute("selected", "selected");
                            await searchProxy(country);
                        }
                        proxyContainer.appendChild(optionElement);
                    }
                }
            } else {
                const proxyHeader = document.querySelector(".proxy__header");
                const caption = proxyHeader.querySelector(".caption");
                const select = proxyHeader.querySelector(".proxy__select");
                caption.classList.add("d-none");
                select.classList.add("d-none");
                startButton.classList.add("d-none");
                const p = document.createElement("p");
                p.textContent = "Free configs not found yet..."
            }
        }

          async function getActiveProxies() {
            overlay.classList.remove("d-none");
            const activeProxy = await getData(MAIN_URL, "proxy/proxies/", jwt);
            console.log(activeProxy);
            const activeProxyElement = document.querySelector(".proxy__table");
            const proxyCount = document.querySelector(".proxy__count");
            activeProxyElement.innerHTML = "";
            
            if (activeProxy["proxies"] && activeProxy["proxies"].length > 0) {
                if (activeProxy["proxies"].length === 10) {
                    startButton.classList.add("button__disabled");
                }
                proxyCount.textContent = activeProxy["proxies"].length;

                for (const proxy of activeProxy["proxies"]) {
                    const proxyList = proxy["proxy"];
                    const ip = proxy["ip"];
                    const port = proxy["port"];
                    const login = proxy["login"];
                    const password = proxy["password"];
                    const adapter = proxy["adapter"];
                    let locationCode = proxy["location_code"].toLowerCase();
                    const proxyTypes = ["http", "socks5"];
                    
                    const proxyDict = {
                      "http": `http://${login}:${password}@${ip}:${port + 10}`,
                      "socks5": `socks5://${login}:${password}@${ip}:${port}`
                    };

                    const fullProxy = `://${login}:${password}@${ip}:${port}`;
                    const speed = proxy["ping"] + "ms";

                    const proxyData = [locationCode, fullProxy, speed, proxyTypes];

                    const tr = document.createElement("tr");
                    tr.setAttribute("data-proxy", JSON.stringify(proxyDict));
                    for (let i = 0; i < proxyData.length; i++) {
                        const data = proxyData[i];
                        const td = document.createElement("td");

                        if (i === 0) {
                            const span = document.createElement("span")
                            if (locationCode == "uk") {
                              locationCode = "gb";
                            }
                            span.setAttribute("class", `fi fi-${locationCode}`);
                            td.appendChild(span);
                        } else if(i === 1) {
                          td.innerText = proxyDict["http"];
                          td.setAttribute("class", "proxy__value");                        
                        } else if (data.includes("http") && data.includes("socks5")) {
                           const typeSelect = document.createElement("select");
                           for (let j = 0; j < proxyTypes.length; j++) {
                             const currentType = proxyTypes[j];
                             const typeOption = document.createElement("option");
                             typeOption.textContent = currentType;
                             typeOption.setAttribute("value", currentType);
                             typeSelect.appendChild(typeOption);
                           }                           
                           td.appendChild(typeSelect);
                           typeSelect.addEventListener("change", (e) => {
                             const newValue = e.target.value;
                             console.log(newValue);
                             const proxyValueElement = tr.querySelector(".proxy__value");
                             proxyValueElement.textContent = proxyDict[newValue];
                           });
                        } else {
                            td.innerText = data;
                        }
                        tr.appendChild(td);
                    }

                    const td = document.createElement("td");
                    const button = document.createElement("button");
                    button.classList.add("button__proxy");
                    button.classList.add("button__proxy-stop")
                    button.textContent = "Turn off";
                    button.addEventListener("click", async () => {
                        button.setAttribute("disabled", "disabled");
                        await stopProxy(MAIN_URL, "proxy/stop/", adapter, jwt);
                        notification.textContent = "Proxy online";
                        notification.classList.remove("d-none")
                        setTimeout(() => {
                          notification.classList.add("d-none");
                        },3000);
                        await getActiveProxies();
                        //document.location.reload();

                    });
                    td.appendChild(button);
                    tr.appendChild(td);
                    activeProxyElement.appendChild(tr);
                }
                overlay.classList.add("d-none");
            } else {
              overlay.classList.add("d-none");
              proxyCount.textContent = activeProxy["proxies"].length;
            }
        }

        // init actions
        errorClose.addEventListener("click", () => {
            errorElement.classList.add("d-none");
        });


        await getLocales();
        await getActiveProxies();

        searchButton.addEventListener("click", async () => {
            await searchProxy();
        });
        startButton.addEventListener("click", async () => {
            await start();
        });
    }

    async function stopProxy(url, apiPath, adapter, jwt) {
        apiPath = `proxy/stop/${adapter}`
        const response = await getData(url, apiPath, jwt);
        return response;
    }

    async function startProxy(url, apiPath, configName, folderName, jwt) {
        apiPath = "proxy/start/"
        const response = await fetch(`${url}${apiPath}`, {
          method: "POST",
          headers: {
              "Authorization": `Bearer ${jwt}`,
              "Content-type": "application/json"
          },
          body: JSON.stringify(
            {
              "config_name": configName,
              "folder_name": folderName
            }
          )
        })
        return response;
    }

    async function getData(url, apiPath, jwt) {
        const response = await fetch(`${url}${apiPath}`, {
          headers: {
            "Authorization": `Bearer ${jwt}`
          }
        });
        const result = await response.json();
        return result;
    }

    main();
});
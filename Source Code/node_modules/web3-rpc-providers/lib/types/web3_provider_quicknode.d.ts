import { Transport, Network } from "./types.js";
import { Web3ExternalProvider } from "./web3_provider.js";
export declare class QuickNodeProvider extends Web3ExternalProvider {
    constructor(network?: Network, transport?: Transport, token?: string, host?: string);
    getRPCURL(network: Network, transport: Transport, _token: string, _host: string): string;
}
//# sourceMappingURL=web3_provider_quicknode.d.ts.map
import withPWAInit from "@ducanh2912/next-pwa";

const withPWA = withPWAInit({
    dest: "public",
    disable: process.env.NODE_ENV === "development",
    register: true,
    skipWaiting: true,
});

const nextConfig = {
    turbopack: {},
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: '/api/index',
            },
        ];
    },
};

export default withPWA(nextConfig);

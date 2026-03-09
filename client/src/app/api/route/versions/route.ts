import { revalidatePath } from "next/cache";
import { NextResponse  } from "next/server";

export async function GET() {
    try {
        const response = await fetch('https://api.papermc.io/v2/projects/paper', {next: {revalidate: 3600}});

        if (!response.ok) {
            throw new Error(`PaperMC API failed with status: ${response.status}`);
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Backend Proxy Failed:", error);
        return NextResponse.json({
            versions: ['LATEST', '1.21.1', '1.21', '1.20.6', '1.20.4', '1.20.1', '1.19.4', '1.18.2']
        });
    }
}